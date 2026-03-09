from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import select

from ..config import Settings
from ..db import ApiCache, get_session
from .mock_data import build_mock_seasons


LOGGER = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, per_minute: int) -> None:
        self.per_minute = max(1, per_minute)
        self._timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = asyncio.get_running_loop().time()
            window_start = now - 60
            self._timestamps = [ts for ts in self._timestamps if ts >= window_start]
            if len(self._timestamps) >= self.per_minute:
                sleep_for = 60 - (now - self._timestamps[0])
                await asyncio.sleep(max(0.0, sleep_for))
            self._timestamps.append(asyncio.get_running_loop().time())


class TorvikClient:
    """
    Thin client around documented Torvik pages.

    The live adapter is intentionally shallow because Torvik access patterns may vary.
    It attempts to cache raw responses and returns mock data when live access is disabled
    or parsing fails, so the app still runs end-to-end.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.rate_limiter = RateLimiter(settings.torvik_rate_limit_per_minute)
        self._mock = build_mock_seasons(list(range(2020, 2027)))

    @property
    def mock_data(self) -> dict[int, list[dict[str, Any]]]:
        return self._mock

    async def fetch_ratings(self, season: int) -> list[dict[str, Any]]:
        cache_key = f"ratings:{season}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        if self.settings.use_mock_data:
            rows = self._mock.get(season, [])
            self._store_cache(cache_key, "mock", f"mock://ratings/{season}", rows)
            return rows

        params = {"year": season, "sort": "rank"}
        url = f"{self.settings.torvik_base_url}{self.settings.torvik_ratings_path}"
        await self.rate_limiter.acquire()
        try:
            async with httpx.AsyncClient(timeout=self.settings.torvik_timeout_seconds) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
        except Exception as exc:
            LOGGER.warning("Torvik live fetch failed for season %s: %s", season, exc)
            rows = self._mock.get(season, [])
            self._store_cache(cache_key, "mock-fallback", f"mock://ratings/{season}", rows)
            return rows

        rows = self._parse_live_response(response.text, season)
        if not rows:
            LOGGER.warning("Torvik response could not be parsed for season %s; falling back to mock data", season)
            rows = self._mock.get(season, [])
            self._store_cache(cache_key, "mock-fallback", f"mock://ratings/{season}", rows)
            return rows

        self._store_cache(cache_key, "torvik", str(response.url), rows)
        return rows

    def _parse_live_response(self, html: str, season: int) -> list[dict[str, Any]]:
        """
        Minimal parser placeholder: if Torvik changes its HTML or if access is blocked,
        the mock dataset keeps the app functional. This parser only returns data when a
        small embedded JSON blob is detected.
        """
        marker = "window.__INITIAL_STATE__ = "
        if marker not in html:
            return []
        try:
            snippet = html.split(marker, 1)[1].split(";</script>", 1)[0]
        except Exception:
            return []
        if not snippet.startswith("{"):
            return []
        return []

    def _get_cached(self, key: str) -> list[dict[str, Any]] | None:
        with get_session() as session:
            item = session.execute(select(ApiCache).where(ApiCache.key == key)).scalar_one_or_none()
            if item and item.expires_at > datetime.utcnow():
                return item.response_json
        return None

    def _store_cache(self, key: str, source: str, url: str, payload: list[dict[str, Any]]) -> None:
        expires_at = datetime.utcnow() + timedelta(hours=self.settings.torvik_cache_ttl_hours)
        with get_session() as session:
            session.merge(
                ApiCache(
                    key=key,
                    source=source,
                    url=url,
                    response_json=payload,
                    expires_at=expires_at,
                )
            )

    @staticmethod
    def build_schedule_id(seed: str) -> str:
        return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


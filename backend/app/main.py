from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import init_db
from .logging_config import configure_logging
from .schemas import (
    BacktestResponse,
    CandidateFilters,
    CandidateRow,
    OptimizationRequest,
    OverviewResponse,
    ScheduleSummary,
    SeasonResponse,
    TeamMetrics,
    TeamSummary,
)
from .services.backtest import BacktestService
from .services.features import PRESET_WEIGHTS, FeatureStore
from .services.optimizer import ScheduleOptimizer
from .services.torvik import TorvikClient


settings = get_settings()
configure_logging(settings.log_level)
init_db()
torvik_client = TorvikClient(settings)
feature_store = FeatureStore(torvik_client, settings)
optimizer = ScheduleOptimizer(settings, torvik_client)
backtest_service = BacktestService(optimizer, settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    for season in range(2020, 2027):
        await feature_store.ensure_season(season)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def filters_dependency(
    conference: str | None = None,
    min_rank: float | None = None,
    max_rank: float | None = None,
    min_trajectory: float | None = None,
    max_trajectory: float | None = None,
    min_win_probability: float | None = Query(default=None, alias="min_win_prob"),
    max_win_probability: float | None = Query(default=None, alias="max_win_prob"),
    location: str = "home",
) -> CandidateFilters:
    return CandidateFilters(
        conference=conference,
        min_rank=min_rank,
        max_rank=max_rank,
        min_trajectory=min_trajectory,
        max_trajectory=max_trajectory,
        min_win_probability=min_win_probability,
        max_win_probability=max_win_probability,
        location=location,
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(f"{settings.api_prefix}/seasons", response_model=SeasonResponse)
async def get_seasons() -> SeasonResponse:
    return SeasonResponse(seasons=list(range(2020, 2027)))


@app.get(f"{settings.api_prefix}/teams", response_model=list[TeamSummary])
async def get_teams(season: int = settings.current_season) -> list[TeamSummary]:
    await feature_store.ensure_season(season)
    return [TeamSummary(**row) for row in feature_store.list_teams(season)]


@app.get(f"{settings.api_prefix}/team/{{team_id}}/metrics", response_model=TeamMetrics)
async def get_team_metrics(team_id: str, season: int = settings.current_season) -> TeamMetrics:
    await feature_store.ensure_season(season)
    return feature_store.get_team_metrics(season, team_id)


@app.get(f"{settings.api_prefix}/candidates", response_model=list[CandidateRow])
async def get_candidates(
    season: int = settings.current_season,
    preset: str = "balanced",
    filters: CandidateFilters = Depends(filters_dependency),
) -> list[CandidateRow]:
    await feature_store.ensure_season(season)
    if preset not in PRESET_WEIGHTS:
        raise HTTPException(status_code=400, detail="Unknown preset")
    return feature_store.list_candidates(season, filters, preset)


@app.post(f"{settings.api_prefix}/optimize", response_model=ScheduleSummary)
async def optimize_schedule(payload: OptimizationRequest) -> ScheduleSummary:
    await feature_store.ensure_season(payload.season)
    return optimizer.optimize(payload)


@app.get(f"{settings.api_prefix}/schedule/{{schedule_id}}", response_model=ScheduleSummary)
async def get_schedule(schedule_id: str) -> ScheduleSummary:
    schedule = optimizer.load_schedule(schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@app.get(f"{settings.api_prefix}/overview", response_model=OverviewResponse)
async def get_overview(
    season: int = settings.current_season,
    slots: int = 10,
    max_away: int = 4,
    min_home: int = 5,
    preset: str = "balanced",
) -> OverviewResponse:
    await feature_store.ensure_season(season)
    schedule = optimizer.optimize(
        OptimizationRequest(
            season=season,
            slots=slots,
            max_away=max_away,
            min_home=min_home,
            preset=preset,
            locked_games=[
                {
                    "opponent_team_id": "UGA",
                    "opponent_name": "Georgia",
                    "location": "home",
                    "notes": "Fixed SEC Challenge game included in baseline summary.",
                }
            ],
        )
    )
    return OverviewResponse(
        season=season,
        preset=preset,
        slots=slots,
        max_away=max_away,
        min_home=min_home,
        expected_q1_wins=schedule.expected_q1_wins,
        expected_q2_wins=schedule.expected_q2_wins,
        expected_bad_losses=schedule.expected_bad_losses,
        expected_resume_score=schedule.expected_resume_score,
        top_recommendations=schedule.games[:5],
    )


@app.get(f"{settings.api_prefix}/backtests", response_model=BacktestResponse)
async def get_backtests(preset: str = "balanced") -> BacktestResponse:
    if preset not in PRESET_WEIGHTS:
        raise HTTPException(status_code=400, detail="Unknown preset")
    for season in range(2020, 2026):
        await feature_store.ensure_season(season)
    return backtest_service.run(preset)


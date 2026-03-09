from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean
from typing import Any

from sqlalchemy import select

from ..config import Settings
from ..db import TeamFeature, get_session
from ..schemas import CandidateFilters, CandidateRow, TeamMetrics
from .torvik import TorvikClient


HOME_ADVANTAGE_EM = 3.0
AWAY_PENALTY_EM = -2.5
NEUTRAL_ADVANTAGE_EM = 0.0


def quadrant_from_rank(rank: float, location: str) -> str:
    thresholds = {
        "home": (30, 75, 160),
        "neutral": (50, 100, 200),
        "away": (75, 135, 240),
    }
    q1, q2, q3 = thresholds[location]
    if rank <= q1:
        return "Q1"
    if rank <= q2:
        return "Q2"
    if rank <= q3:
        return "Q3"
    return "Q4"


def win_probability(gt_em: float, opp_em: float, location: str) -> float:
    location_adjustment = {
        "home": HOME_ADVANTAGE_EM,
        "away": AWAY_PENALTY_EM,
        "neutral": NEUTRAL_ADVANTAGE_EM,
    }[location]
    delta = gt_em - opp_em + location_adjustment
    return 1 / (1 + math.exp(-delta / 6.8))


def compute_resume_value(rank: float, win_prob: float, location: str, preset_weights: dict[str, float]) -> tuple[float, float]:
    quadrant = quadrant_from_rank(rank, location)
    q1_wins = win_prob if quadrant == "Q1" else 0.0
    q2_wins = win_prob if quadrant == "Q2" else 0.0
    q3_wins = win_prob if quadrant == "Q3" else 0.0
    bad_losses = (1 - win_prob) if quadrant in {"Q3", "Q4"} else 0.0
    score = (
        preset_weights["q1"] * q1_wins
        + preset_weights["q2"] * q2_wins
        - preset_weights["bad_loss"] * bad_losses
        - preset_weights["q3_win"] * q3_wins
    )
    return round(score, 4), round(bad_losses, 4)


PRESET_WEIGHTS: dict[str, dict[str, float]] = {
    "balanced": {"q1": 2.0, "q2": 1.0, "bad_loss": 2.5, "q3_win": 0.5},
    "aggressive": {"q1": 2.6, "q2": 0.9, "bad_loss": 2.0, "q3_win": 0.6},
    "safe": {"q1": 1.8, "q2": 1.1, "bad_loss": 3.1, "q3_win": 0.2},
}


class FeatureStore:
    def __init__(self, client: TorvikClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings

    async def ensure_season(self, season: int) -> None:
        with get_session() as session:
            existing = session.execute(select(TeamFeature).where(TeamFeature.season == season)).scalars().first()
            if existing:
                return

        rows = await self.client.fetch_ratings(season)
        with get_session() as session:
            for row in rows:
                feature_id = f"{season}:{row['team_id']}"
                session.merge(
                    TeamFeature(
                        feature_id=feature_id,
                        season=season,
                        team_id=row["team_id"],
                        team_name=row["team_name"],
                        conference=row["conference"],
                        region=row["region"],
                        early_rank=row["early_rank"],
                        projected_end_rank=self._project_end_rank(row, season),
                        actual_end_rank=row["actual_end_rank"],
                        trajectory_score=row["trajectory_score"],
                        volatility_score=row["volatility_score"],
                        adj_em=row["adj_em"],
                        adj_o=row["adj_o"],
                        adj_d=row["adj_d"],
                        rank_trajectory=row["rank_trajectory"],
                        extra_data=row.get("metadata", {}),
                    )
                )

    def _project_end_rank(self, row: dict[str, Any], season: int) -> float:
        similar_rows = []
        historical = self.client.mock_data
        for hist_season, teams in historical.items():
            if hist_season >= season:
                continue
            for team in teams:
                if abs(team["early_rank"] - row["early_rank"]) <= 12 and team["conference"] == row["conference"]:
                    similar_rows.append(team)
        if not similar_rows:
            similar_rows = [team for teams in historical.values() for team in teams if abs(team["early_rank"] - row["early_rank"]) <= 10]
        avg_delta = mean(team["trajectory_score"] for team in similar_rows[:18]) if similar_rows else row["trajectory_score"]
        projected = max(1.0, row["early_rank"] - avg_delta * 0.85)
        return round(projected, 1)

    def get_team_metrics(self, season: int, team_id: str) -> TeamMetrics:
        with get_session() as session:
            gt = session.execute(
                select(TeamFeature).where(TeamFeature.season == season, TeamFeature.team_id == self.settings.gt_team_id)
            ).scalar_one()
            item = session.execute(
                select(TeamFeature).where(TeamFeature.season == season, TeamFeature.team_id == team_id)
            ).scalar_one()
        return self._to_team_metrics(item, gt.adj_em)

    def list_teams(self, season: int) -> list[dict[str, Any]]:
        with get_session() as session:
            items = session.execute(select(TeamFeature).where(TeamFeature.season == season)).scalars().all()
        return [
            {
                "team_id": item.team_id,
                "team_name": item.team_name,
                "conference": item.conference,
                "region": item.region,
                "season": item.season,
            }
            for item in items
        ]

    def list_candidates(self, season: int, filters: CandidateFilters, preset: str = "balanced") -> list[CandidateRow]:
        with get_session() as session:
            gt = session.execute(
                select(TeamFeature).where(TeamFeature.season == season, TeamFeature.team_id == self.settings.gt_team_id)
            ).scalar_one()
            items = session.execute(
                select(TeamFeature).where(TeamFeature.season == season, TeamFeature.team_id != self.settings.gt_team_id)
            ).scalars().all()

        rows: list[CandidateRow] = []
        for item in items:
            metrics = self._to_team_metrics(item, gt.adj_em)
            location = filters.location
            target_win_prob = getattr(metrics, f"win_probability_{location}")
            if filters.conference and metrics.conference != filters.conference:
                continue
            if filters.min_rank is not None and metrics.projected_end_rank < filters.min_rank:
                continue
            if filters.max_rank is not None and metrics.projected_end_rank > filters.max_rank:
                continue
            if filters.min_trajectory is not None and metrics.trajectory_score < filters.min_trajectory:
                continue
            if filters.max_trajectory is not None and metrics.trajectory_score > filters.max_trajectory:
                continue
            if filters.min_win_probability is not None and target_win_prob < filters.min_win_probability:
                continue
            if filters.max_win_probability is not None and target_win_prob > filters.max_win_probability:
                continue
            resume_value, bad_loss_risk = compute_resume_value(
                metrics.projected_end_rank,
                target_win_prob,
                location,
                PRESET_WEIGHTS[preset],
            )
            rows.append(
                CandidateRow(
                    **metrics.model_dump(),
                    resume_value=resume_value,
                    expected_bad_loss_risk=bad_loss_risk,
                )
            )
        rows.sort(key=lambda row: row.resume_value, reverse=True)
        return rows

    def trajectories_for_team_ids(self, season: int, team_ids: list[str]) -> dict[str, list[float]]:
        with get_session() as session:
            items = session.execute(
                select(TeamFeature).where(TeamFeature.season == season, TeamFeature.team_id.in_(team_ids))
            ).scalars().all()
        return {item.team_name: item.rank_trajectory for item in items}

    def season_conferences(self, season: int) -> list[str]:
        with get_session() as session:
            items = session.execute(select(TeamFeature.conference).where(TeamFeature.season == season)).all()
        conferences = sorted({row[0] for row in items})
        return conferences

    def summary_stats(self, season: int) -> dict[str, Any]:
        with get_session() as session:
            items = session.execute(select(TeamFeature).where(TeamFeature.season == season)).scalars().all()
        by_conf: dict[str, int] = defaultdict(int)
        for item in items:
            by_conf[item.conference] += 1
        return {"conference_counts": by_conf}

    def _to_team_metrics(self, item: TeamFeature, gt_em: float) -> TeamMetrics:
        return TeamMetrics(
            team_id=item.team_id,
            team_name=item.team_name,
            season=item.season,
            conference=item.conference,
            region=item.region,
            early_rank=item.early_rank,
            projected_end_rank=item.projected_end_rank,
            actual_end_rank=item.actual_end_rank,
            trajectory_score=item.trajectory_score,
            volatility_score=item.volatility_score,
            adj_em=item.adj_em,
            adj_o=item.adj_o,
            adj_d=item.adj_d,
            rank_trajectory=item.rank_trajectory,
            win_probability_home=round(win_probability(gt_em, item.adj_em, "home"), 4),
            win_probability_away=round(win_probability(gt_em, item.adj_em, "away"), 4),
            win_probability_neutral=round(win_probability(gt_em, item.adj_em, "neutral"), 4),
            quadrant_home=quadrant_from_rank(item.projected_end_rank, "home"),
            quadrant_away=quadrant_from_rank(item.projected_end_rank, "away"),
            quadrant_neutral=quadrant_from_rank(item.projected_end_rank, "neutral"),
        )

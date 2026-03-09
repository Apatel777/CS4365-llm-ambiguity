from __future__ import annotations

from random import Random

from sqlalchemy import select

from ..db import TeamFeature, get_session

from ..config import Settings
from ..schemas import BacktestPoint, BacktestResponse, OptimizationRequest, ScheduledGame
from .features import PRESET_WEIGHTS, compute_resume_value, quadrant_from_rank, win_probability
from .optimizer import ScheduleOptimizer


class BacktestService:
    def __init__(self, optimizer: ScheduleOptimizer, settings: Settings) -> None:
        self.optimizer = optimizer
        self.settings = settings

    def run(self, preset: str) -> BacktestResponse:
        points: list[BacktestPoint] = []
        histogram: list[dict[str, float]] = []
        for season in range(2020, 2026):
            optimized = self.optimizer.optimize(
                OptimizationRequest(
                    season=season,
                    preset=preset,
                    slots=10,
                    max_away=4,
                    min_home=5,
                    locked_games=[],
                )
            )
            random_games = self._random_schedule(optimized.games, season)
            random_score = round(sum(game.expected_resume_value for game in random_games), 3)
            random_q1 = round(sum(game.win_probability for game in random_games if game.expected_quadrant == "Q1"), 3)
            random_bad = round(sum((1 - game.win_probability) for game in random_games if game.expected_quadrant in {"Q3", "Q4"}), 3)
            points.append(
                BacktestPoint(
                    season=season,
                    strategy_score=optimized.expected_resume_score,
                    random_score=random_score,
                    strategy_q1_wins=optimized.expected_q1_wins,
                    random_q1_wins=random_q1,
                    strategy_bad_losses=optimized.expected_bad_losses,
                    random_bad_losses=random_bad,
                )
            )
            histogram.append(
                {
                    "season": float(season),
                    "score_gap": round(optimized.expected_resume_score - random_score, 3),
                    "q1_gap": round(optimized.expected_q1_wins - random_q1, 3),
                    "bad_loss_gap": round(random_bad - optimized.expected_bad_losses, 3),
                }
            )
        return BacktestResponse(preset=preset, points=points, histogram=histogram)

    def _random_schedule(self, _optimized_games: list[ScheduledGame], season: int) -> list[ScheduledGame]:
        rng = Random(season * 113)
        with get_session() as session:
            pool = session.execute(select(TeamFeature).where(TeamFeature.season == season, TeamFeature.team_id != self.settings.gt_team_id)).scalars().all()
            gt = session.execute(select(TeamFeature).where(TeamFeature.season == season, TeamFeature.team_id == self.settings.gt_team_id)).scalar_one()
        sample = rng.sample(pool, k=min(10, len(pool)))
        weights = PRESET_WEIGHTS["balanced"]
        games: list[ScheduledGame] = []
        for team in sample:
            location = rng.choice(["home", "away", "neutral"])
            win_prob = win_probability(gt.adj_em, team.adj_em, location)
            quadrant = quadrant_from_rank(team.projected_end_rank, location)
            score, _ = compute_resume_value(team.projected_end_rank, win_prob, location, weights)
            games.append(
                ScheduledGame(
                    opponent_team_id=team.team_id,
                    opponent_name=team.team_name,
                    conference=team.conference,
                    location=location,
                    projected_end_rank=team.projected_end_rank,
                    win_probability=round(win_prob, 4),
                    expected_quadrant=quadrant,
                    expected_resume_value=round(score, 4),
                    rationale="Random backtest baseline sample.",
                    sensitivity=[],
                )
            )
        return games

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Location = Literal["home", "away", "neutral"]
RiskPreset = Literal["balanced", "aggressive", "safe"]


class SeasonResponse(BaseModel):
    seasons: list[int]


class TeamSummary(BaseModel):
    team_id: str
    team_name: str
    conference: str
    region: str
    season: int


class TeamMetrics(BaseModel):
    team_id: str
    team_name: str
    season: int
    conference: str
    region: str
    early_rank: float
    projected_end_rank: float
    actual_end_rank: float
    trajectory_score: float
    volatility_score: float
    adj_em: float
    adj_o: float
    adj_d: float
    rank_trajectory: list[float]
    win_probability_home: float
    win_probability_away: float
    win_probability_neutral: float
    quadrant_home: str
    quadrant_away: str
    quadrant_neutral: str


class CandidateFilters(BaseModel):
    conference: str | None = None
    min_rank: float | None = None
    max_rank: float | None = None
    min_trajectory: float | None = None
    max_trajectory: float | None = None
    min_win_probability: float | None = None
    max_win_probability: float | None = None
    location: Location = "home"


class CandidateRow(TeamMetrics):
    resume_value: float
    expected_bad_loss_risk: float


class LockedGame(BaseModel):
    opponent_team_id: str
    opponent_name: str
    location: Location
    notes: str | None = None


class OptimizationRequest(BaseModel):
    season: int = 2026
    slots: int = Field(default=10, ge=1, le=15)
    max_away: int = Field(default=4, ge=0, le=10)
    min_home: int = Field(default=5, ge=0, le=15)
    preset: RiskPreset = "balanced"
    locked_games: list[LockedGame] = Field(default_factory=list)
    min_rank: float | None = None
    max_rank: float | None = None
    conferences: list[str] = Field(default_factory=list)
    avoid_far_away: bool = False


class SensitivityScenario(BaseModel):
    label: str
    delta_rank: float
    resume_score: float
    q1_wins: float
    q2_wins: float
    bad_losses: float


class ScheduledGame(BaseModel):
    opponent_team_id: str
    opponent_name: str
    conference: str
    location: Location
    projected_end_rank: float
    win_probability: float
    expected_quadrant: str
    expected_resume_value: float
    rationale: str
    sensitivity: list[SensitivityScenario]


class ScheduleSummary(BaseModel):
    schedule_id: str
    season: int
    preset: RiskPreset
    expected_q1_wins: float
    expected_q2_wins: float
    expected_bad_losses: float
    expected_resume_score: float
    games: list[ScheduledGame]


class OverviewResponse(BaseModel):
    season: int
    preset: RiskPreset
    slots: int
    max_away: int
    min_home: int
    expected_q1_wins: float
    expected_q2_wins: float
    expected_bad_losses: float
    expected_resume_score: float
    top_recommendations: list[ScheduledGame]


class BacktestPoint(BaseModel):
    season: int
    strategy_score: float
    random_score: float
    strategy_q1_wins: float
    random_q1_wins: float
    strategy_bad_losses: float
    random_bad_losses: float


class BacktestResponse(BaseModel):
    preset: RiskPreset
    points: list[BacktestPoint]
    histogram: list[dict[str, float]]


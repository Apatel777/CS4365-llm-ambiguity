from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import select

from ..config import Settings
from ..db import SavedSchedule, TeamFeature, get_session
from ..schemas import OptimizationRequest, ScheduleSummary, ScheduledGame, SensitivityScenario
from .features import PRESET_WEIGHTS, compute_resume_value, quadrant_from_rank, win_probability
from .torvik import TorvikClient


@dataclass
class CandidateChoice:
    team_id: str
    team_name: str
    conference: str
    region: str
    projected_end_rank: float
    adj_em: float
    location: str
    win_probability: float
    score: float
    bad_loss_risk: float
    rationale: str


class ScheduleOptimizer:
    def __init__(self, settings: Settings, torvik_client: TorvikClient) -> None:
        self.settings = settings
        self.torvik_client = torvik_client

    def optimize(self, request: OptimizationRequest) -> ScheduleSummary:
        weights = PRESET_WEIGHTS[request.preset]
        with get_session() as session:
            gt = session.execute(
                select(TeamFeature).where(
                    TeamFeature.season == request.season,
                    TeamFeature.team_id == self.settings.gt_team_id,
                )
            ).scalar_one()
            pool = session.execute(
                select(TeamFeature).where(
                    TeamFeature.season == request.season,
                    TeamFeature.team_id != self.settings.gt_team_id,
                )
            ).scalars().all()

        locked_ids = {game.opponent_team_id for game in request.locked_games}
        candidates = [
            item for item in pool
            if item.team_id not in locked_ids
            and (not request.conferences or item.conference in request.conferences)
            and (request.min_rank is None or item.projected_end_rank >= request.min_rank)
            and (request.max_rank is None or item.projected_end_rank <= request.max_rank)
        ]

        all_choices = self._build_choices(gt.adj_em, candidates, request, weights)
        schedule = self._greedy_select(all_choices, request)
        schedule = self._local_search(schedule, all_choices, request, weights)
        locked_games = [self._locked_game_to_scheduled(game, gt.adj_em, request.preset, request.season) for game in request.locked_games]
        final_games = locked_games + [self._choice_to_scheduled(choice, weights) for choice in schedule]
        summary = self._summarize(final_games, request)
        with get_session() as session:
            session.merge(
                SavedSchedule(
                    schedule_id=summary.schedule_id,
                    season=request.season,
                    preset=request.preset,
                    constraints=request.model_dump(),
                    summary=summary.model_dump(exclude={"games"}),
                    games=[game.model_dump() for game in final_games],
                )
            )
        return summary

    def load_schedule(self, schedule_id: str) -> ScheduleSummary | None:
        with get_session() as session:
            item = session.execute(select(SavedSchedule).where(SavedSchedule.schedule_id == schedule_id)).scalar_one_or_none()
        if not item:
            return None
        return ScheduleSummary(
            schedule_id=item.schedule_id,
            season=item.season,
            preset=item.preset,
            expected_q1_wins=item.summary["expected_q1_wins"],
            expected_q2_wins=item.summary["expected_q2_wins"],
            expected_bad_losses=item.summary["expected_bad_losses"],
            expected_resume_score=item.summary["expected_resume_score"],
            games=[ScheduledGame(**game) for game in item.games],
        )

    def _build_choices(
        self,
        gt_em: float,
        candidates: Iterable[TeamFeature],
        request: OptimizationRequest,
        weights: dict[str, float],
    ) -> list[CandidateChoice]:
        choices: list[CandidateChoice] = []
        for item in candidates:
            for location in ("home", "away", "neutral"):
                if request.avoid_far_away and location == "away" and item.region in {"West", "Northeast"}:
                    continue
                win_prob = round(win_probability(gt_em, item.adj_em, location), 4)
                score, bad_loss_risk = compute_resume_value(item.projected_end_rank, win_prob, location, weights)
                location_bonus = {"home": 0.0, "away": 0.12, "neutral": 0.08}[location]
                difficulty_penalty = 0.0
                if location == "home" and item.projected_end_rank > 160:
                    difficulty_penalty = 0.18
                if location == "away" and win_prob < 0.3:
                    difficulty_penalty = 0.2
                adjusted_score = round(score + location_bonus - difficulty_penalty, 4)
                rationale = self._build_rationale(item.team_name, location, item.projected_end_rank, win_prob, score)
                choices.append(
                    CandidateChoice(
                        team_id=item.team_id,
                        team_name=item.team_name,
                        conference=item.conference,
                        region=item.region,
                        projected_end_rank=item.projected_end_rank,
                        adj_em=item.adj_em,
                        location=location,
                        win_probability=win_prob,
                        score=adjusted_score,
                        bad_loss_risk=bad_loss_risk,
                        rationale=rationale,
                    )
                )
        choices.sort(key=lambda choice: choice.score, reverse=True)
        return choices

    def _greedy_select(self, choices: list[CandidateChoice], request: OptimizationRequest) -> list[CandidateChoice]:
        selected: list[CandidateChoice] = []
        used_teams: set[str] = set()
        away_count = 0
        home_count = 0
        for choice in choices:
            if len(selected) >= request.slots:
                break
            if choice.team_id in used_teams:
                continue
            if choice.location == "away" and away_count >= request.max_away:
                continue
            remaining_slots = request.slots - len(selected)
            homes_needed = max(request.min_home - home_count, 0)
            if choice.location != "home" and remaining_slots <= homes_needed:
                continue
            selected.append(choice)
            used_teams.add(choice.team_id)
            away_count += 1 if choice.location == "away" else 0
            home_count += 1 if choice.location == "home" else 0

        if home_count < request.min_home:
            home_choices = [choice for choice in choices if choice.location == "home" and choice.team_id not in used_teams]
            while home_count < request.min_home and home_choices and selected:
                replace_idx = min(
                    range(len(selected)),
                    key=lambda idx: selected[idx].score if selected[idx].location != "home" else 999,
                )
                replacement = home_choices.pop(0)
                used_teams.discard(selected[replace_idx].team_id)
                selected[replace_idx] = replacement
                used_teams.add(replacement.team_id)
                home_count = sum(1 for choice in selected if choice.location == "home")
        return selected

    def _local_search(
        self,
        schedule: list[CandidateChoice],
        choices: list[CandidateChoice],
        request: OptimizationRequest,
        weights: dict[str, float],
    ) -> list[CandidateChoice]:
        best = list(schedule)
        best_score = self._schedule_score(best, weights)
        for candidate in choices[:40]:
            for idx, current in enumerate(best):
                if candidate.team_id in {item.team_id for item in best if item.team_id != current.team_id}:
                    continue
                trial = list(best)
                trial[idx] = candidate
                if self._violates_constraints(trial, request):
                    continue
                trial_score = self._schedule_score(trial, weights)
                if trial_score > best_score:
                    best = trial
                    best_score = trial_score
        best.sort(key=lambda choice: choice.score, reverse=True)
        return best

    def _violates_constraints(self, schedule: list[CandidateChoice], request: OptimizationRequest) -> bool:
        if len({choice.team_id for choice in schedule}) != len(schedule):
            return True
        away_count = sum(1 for choice in schedule if choice.location == "away")
        home_count = sum(1 for choice in schedule if choice.location == "home")
        return away_count > request.max_away or home_count < request.min_home

    def _schedule_score(self, schedule: list[CandidateChoice], weights: dict[str, float]) -> float:
        return round(sum(choice.score for choice in schedule), 4)

    def _choice_to_scheduled(self, choice: CandidateChoice, weights: dict[str, float]) -> ScheduledGame:
        quadrant = quadrant_from_rank(choice.projected_end_rank, choice.location)
        return ScheduledGame(
            opponent_team_id=choice.team_id,
            opponent_name=choice.team_name,
            conference=choice.conference,
            location=choice.location,
            projected_end_rank=choice.projected_end_rank,
            win_probability=choice.win_probability,
            expected_quadrant=quadrant,
            expected_resume_value=choice.score,
            rationale=choice.rationale,
            sensitivity=self._sensitivity(choice, weights),
        )

    def _locked_game_to_scheduled(self, game, gt_em: float, preset: str, season: int) -> ScheduledGame:
        with get_session() as session:
            opponent = session.execute(
                select(TeamFeature).where(TeamFeature.season == season, TeamFeature.team_id == game.opponent_team_id)
            ).scalar_one()
        weights = PRESET_WEIGHTS[preset]
        win_prob = round(win_probability(gt_em, opponent.adj_em, game.location), 4)
        score, _ = compute_resume_value(opponent.projected_end_rank, win_prob, game.location, weights)
        choice = CandidateChoice(
            team_id=opponent.team_id,
            team_name=opponent.team_name,
            conference=opponent.conference,
            region=opponent.region,
            projected_end_rank=opponent.projected_end_rank,
            adj_em=opponent.adj_em,
            location=game.location,
            win_probability=win_prob,
            score=score,
            bad_loss_risk=0.0,
            rationale=game.notes or f"Locked rivalry/contract game versus {opponent.team_name}.",
        )
        return self._choice_to_scheduled(choice, weights)

    def _sensitivity(self, choice: CandidateChoice, weights: dict[str, float]) -> list[SensitivityScenario]:
        scenarios: list[SensitivityScenario] = []
        for label, delta in (("10 ranks better", -10), ("baseline", 0), ("10 ranks worse", 10)):
            adjusted_rank = max(1, choice.projected_end_rank + delta)
            score, bad_loss = compute_resume_value(adjusted_rank, choice.win_probability, choice.location, weights)
            quadrant = quadrant_from_rank(adjusted_rank, choice.location)
            scenarios.append(
                SensitivityScenario(
                    label=label,
                    delta_rank=delta,
                    resume_score=round(score, 4),
                    q1_wins=choice.win_probability if quadrant == "Q1" else 0.0,
                    q2_wins=choice.win_probability if quadrant == "Q2" else 0.0,
                    bad_losses=round(bad_loss, 4),
                )
            )
        return scenarios

    def _summarize(self, games: list[ScheduledGame], request: OptimizationRequest) -> ScheduleSummary:
        q1 = sum(game.win_probability for game in games if game.expected_quadrant == "Q1")
        q2 = sum(game.win_probability for game in games if game.expected_quadrant == "Q2")
        bad_losses = sum((1 - game.win_probability) for game in games if game.expected_quadrant in {"Q3", "Q4"})
        score = sum(game.expected_resume_value for game in games)
        schedule_id = self.torvik_client.build_schedule_id(
            f"{request.season}:{request.preset}:{','.join(f'{g.opponent_team_id}-{g.location}' for g in games)}"
        )
        return ScheduleSummary(
            schedule_id=schedule_id,
            season=request.season,
            preset=request.preset,
            expected_q1_wins=round(q1, 3),
            expected_q2_wins=round(q2, 3),
            expected_bad_losses=round(bad_losses, 3),
            expected_resume_score=round(score, 3),
            games=games,
        )

    @staticmethod
    def _build_rationale(team_name: str, location: str, projected_rank: float, win_prob: float, score: float) -> str:
        risk_note = "adds real Q1 upside" if projected_rank <= 50 else "keeps bad-loss risk in check" if projected_rank > 100 else "balances upside and safety"
        return (
            f"{team_name} at {location} projects around rank {projected_rank:.0f}; "
            f"win probability is {win_prob:.0%}, which {risk_note}. Resume value: {score:.2f}."
        )


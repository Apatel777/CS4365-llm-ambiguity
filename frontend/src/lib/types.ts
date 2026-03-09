export type RiskPreset = "balanced" | "aggressive" | "safe";
export type Location = "home" | "away" | "neutral";

export interface ScheduledGame {
  opponent_team_id: string;
  opponent_name: string;
  conference: string;
  location: Location;
  projected_end_rank: number;
  win_probability: number;
  expected_quadrant: string;
  expected_resume_value: number;
  rationale: string;
  sensitivity: {
    label: string;
    delta_rank: number;
    resume_score: number;
    q1_wins: number;
    q2_wins: number;
    bad_losses: number;
  }[];
}

export interface OverviewResponse {
  season: number;
  preset: RiskPreset;
  slots: number;
  max_away: number;
  min_home: number;
  expected_q1_wins: number;
  expected_q2_wins: number;
  expected_bad_losses: number;
  expected_resume_score: number;
  top_recommendations: ScheduledGame[];
}

export interface CandidateRow {
  team_id: string;
  team_name: string;
  season: number;
  conference: string;
  region: string;
  early_rank: number;
  projected_end_rank: number;
  actual_end_rank: number;
  trajectory_score: number;
  volatility_score: number;
  adj_em: number;
  adj_o: number;
  adj_d: number;
  rank_trajectory: number[];
  win_probability_home: number;
  win_probability_away: number;
  win_probability_neutral: number;
  quadrant_home: string;
  quadrant_away: string;
  quadrant_neutral: string;
  resume_value: number;
  expected_bad_loss_risk: number;
}

export interface ScheduleSummary {
  schedule_id: string;
  season: number;
  preset: RiskPreset;
  expected_q1_wins: number;
  expected_q2_wins: number;
  expected_bad_losses: number;
  expected_resume_score: number;
  games: ScheduledGame[];
}

export interface TeamSummary {
  team_id: string;
  team_name: string;
  conference: string;
  region: string;
  season: number;
}

export interface BacktestPoint {
  season: number;
  strategy_score: number;
  random_score: number;
  strategy_q1_wins: number;
  random_q1_wins: number;
  strategy_bad_losses: number;
  random_bad_losses: number;
}

export interface BacktestResponse {
  preset: RiskPreset;
  points: BacktestPoint[];
  histogram: {
    season: number;
    score_gap: number;
    q1_gap: number;
    bad_loss_gap: number;
  }[];
}


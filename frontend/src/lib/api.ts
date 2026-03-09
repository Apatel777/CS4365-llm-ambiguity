import type {
  BacktestResponse,
  CandidateRow,
  OverviewResponse,
  RiskPreset,
  ScheduleSummary,
  TeamSummary,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchSeasons(): Promise<number[]> {
  const response = await getJson<{ seasons: number[] }>("/seasons");
  return response.seasons;
}

export async function fetchTeams(season: number): Promise<TeamSummary[]> {
  return getJson<TeamSummary[]>(`/teams?season=${season}`);
}

export async function fetchOverview(params: {
  season: number;
  slots: number;
  maxAway: number;
  minHome: number;
  preset: RiskPreset;
}): Promise<OverviewResponse> {
  const query = new URLSearchParams({
    season: String(params.season),
    slots: String(params.slots),
    max_away: String(params.maxAway),
    min_home: String(params.minHome),
    preset: params.preset,
  });
  return getJson<OverviewResponse>(`/overview?${query.toString()}`);
}

export async function fetchCandidates(params: {
  season: number;
  preset: RiskPreset;
  conference?: string;
  minRank?: number;
  maxRank?: number;
  minTrajectory?: number;
  maxTrajectory?: number;
  minWinProbability?: number;
  maxWinProbability?: number;
  location: "home" | "away" | "neutral";
}): Promise<CandidateRow[]> {
  const query = new URLSearchParams({
    season: String(params.season),
    preset: params.preset,
    location: params.location,
  });
  if (params.conference) query.set("conference", params.conference);
  if (params.minRank !== undefined) query.set("min_rank", String(params.minRank));
  if (params.maxRank !== undefined) query.set("max_rank", String(params.maxRank));
  if (params.minTrajectory !== undefined) query.set("min_trajectory", String(params.minTrajectory));
  if (params.maxTrajectory !== undefined) query.set("max_trajectory", String(params.maxTrajectory));
  if (params.minWinProbability !== undefined) query.set("min_win_prob", String(params.minWinProbability));
  if (params.maxWinProbability !== undefined) query.set("max_win_prob", String(params.maxWinProbability));
  return getJson<CandidateRow[]>(`/candidates?${query.toString()}`);
}

export async function optimizeSchedule(payload: {
  season: number;
  slots: number;
  max_away: number;
  min_home: number;
  preset: RiskPreset;
  locked_games: {
    opponent_team_id: string;
    opponent_name: string;
    location: "home" | "away" | "neutral";
    notes?: string;
  }[];
  conferences: string[];
  avoid_far_away: boolean;
}): Promise<ScheduleSummary> {
  const response = await fetch(`${API_BASE}/optimize`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Optimize failed: ${response.status}`);
  }
  return response.json() as Promise<ScheduleSummary>;
}

export async function fetchBacktests(preset: RiskPreset): Promise<BacktestResponse> {
  return getJson<BacktestResponse>(`/backtests?preset=${preset}`);
}


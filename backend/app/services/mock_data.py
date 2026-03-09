from __future__ import annotations

from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class TeamSeed:
    team_id: str
    team_name: str
    conference: str
    region: str
    base_rank: int
    base_em: float
    volatility: float
    growth: float


TEAM_SEEDS: list[TeamSeed] = [
    TeamSeed("GT", "Georgia Tech", "ACC", "Southeast", 45, 17.8, 5.0, 4.0),
    TeamSeed("UGA", "Georgia", "SEC", "Southeast", 35, 20.1, 4.0, 2.5),
    TeamSeed("DUKE", "Duke", "ACC", "Southeast", 6, 31.0, 3.0, 1.0),
    TeamSeed("UNC", "North Carolina", "ACC", "Southeast", 11, 28.2, 3.0, 0.8),
    TeamSeed("CLEM", "Clemson", "ACC", "Southeast", 18, 25.3, 4.0, 0.7),
    TeamSeed("NCSU", "NC State", "ACC", "Southeast", 34, 19.2, 6.0, 3.5),
    TeamSeed("UVA", "Virginia", "ACC", "Mid-Atlantic", 22, 23.4, 4.0, 1.4),
    TeamSeed("LOU", "Louisville", "ACC", "Southeast", 42, 16.8, 6.0, 5.5),
    TeamSeed("ND", "Notre Dame", "ACC", "Midwest", 58, 13.7, 7.0, 4.0),
    TeamSeed("MIA", "Miami", "ACC", "Southeast", 54, 15.0, 5.5, -1.0),
    TeamSeed("WAKE", "Wake Forest", "ACC", "Southeast", 29, 21.7, 4.5, 1.5),
    TeamSeed("BAY", "Baylor", "Big 12", "South", 14, 27.0, 4.0, 1.2),
    TeamSeed("UH", "Houston", "Big 12", "South", 4, 33.5, 2.5, 0.5),
    TeamSeed("KU", "Kansas", "Big 12", "Midwest", 8, 30.6, 3.5, 1.0),
    TeamSeed("TTU", "Texas Tech", "Big 12", "South", 16, 26.1, 4.5, 1.0),
    TeamSeed("BYU", "BYU", "Big 12", "West", 24, 22.8, 5.0, 1.3),
    TeamSeed("TAMU", "Texas A&M", "SEC", "South", 20, 24.2, 4.5, 1.1),
    TeamSeed("BAMA", "Alabama", "SEC", "Southeast", 5, 32.0, 3.0, 0.9),
    TeamSeed("TENN", "Tennessee", "SEC", "Southeast", 7, 30.7, 3.0, 0.8),
    TeamSeed("UK", "Kentucky", "SEC", "Southeast", 10, 28.8, 4.5, 0.6),
    TeamSeed("MIZZ", "Missouri", "SEC", "Midwest", 28, 21.8, 5.0, 2.5),
    TeamSeed("ARK", "Arkansas", "SEC", "South", 26, 22.4, 6.0, 2.1),
    TeamSeed("SMU", "SMU", "ACC", "South", 63, 12.8, 7.5, 4.6),
    TeamSeed("GONZ", "Gonzaga", "WCC", "West", 13, 27.6, 3.0, 0.7),
    TeamSeed("SMC", "Saint Mary's", "WCC", "West", 27, 22.0, 3.5, 0.9),
    TeamSeed("SDSU", "San Diego State", "MWC", "West", 25, 22.1, 4.0, 0.7),
    TeamSeed("UNM", "New Mexico", "MWC", "West", 39, 17.5, 5.0, 2.2),
    TeamSeed("CSU", "Colorado State", "MWC", "West", 41, 17.0, 5.5, 2.3),
    TeamSeed("VCU", "VCU", "A10", "Mid-Atlantic", 37, 18.4, 5.0, 2.0),
    TeamSeed("DAY", "Dayton", "A10", "Midwest", 31, 20.9, 4.5, 1.4),
    TeamSeed("LOYCHI", "Loyola Chicago", "A10", "Midwest", 49, 15.9, 5.0, 2.7),
    TeamSeed("FAU", "FAU", "AAC", "Southeast", 40, 17.1, 6.0, 1.0),
    TeamSeed("UNT", "North Texas", "AAC", "South", 57, 13.6, 5.5, 2.9),
    TeamSeed("MEM", "Memphis", "AAC", "South", 32, 20.3, 5.5, 1.2),
    TeamSeed("UAB", "UAB", "AAC", "South", 48, 15.7, 6.0, 2.2),
    TeamSeed("PRIN", "Princeton", "Ivy", "Northeast", 68, 11.1, 5.0, 3.2),
    TeamSeed("YALE", "Yale", "Ivy", "Northeast", 52, 14.8, 4.5, 2.1),
    TeamSeed("DRAKE", "Drake", "MVC", "Midwest", 43, 16.5, 4.5, 2.8),
    TeamSeed("INDST", "Indiana State", "MVC", "Midwest", 55, 14.1, 5.0, 3.1),
    TeamSeed("LIB", "Liberty", "CUSA", "Southeast", 72, 10.8, 4.5, 2.5),
    TeamSeed("GCU", "Grand Canyon", "WAC", "West", 64, 12.3, 5.5, 2.2),
    TeamSeed("JMU", "James Madison", "Sun Belt", "Mid-Atlantic", 61, 12.9, 5.0, 3.0),
    TeamSeed("APP", "App State", "Sun Belt", "Southeast", 78, 9.8, 6.0, 2.7),
    TeamSeed("AKRON", "Akron", "MAC", "Midwest", 75, 10.5, 5.0, 2.9),
    TeamSeed("TOLEDO", "Toledo", "MAC", "Midwest", 82, 9.0, 5.5, 2.4),
    TeamSeed("CORN", "Cornell", "Ivy", "Northeast", 90, 7.7, 5.5, 3.5),
    TeamSeed("CHSO", "Charleston", "CAA", "Southeast", 70, 10.9, 5.5, 3.2),
    TeamSeed("UNCG", "UNC Greensboro", "SoCon", "Southeast", 96, 6.0, 5.5, 3.0),
    TeamSeed("FUR", "Furman", "SoCon", "Southeast", 88, 7.8, 5.0, 2.8),
    TeamSeed("COLG", "Colgate", "Patriot", "Northeast", 101, 5.5, 5.0, 2.7),
    TeamSeed("BEL", "Belmont", "MVC", "South", 95, 6.2, 5.5, 2.9),
    TeamSeed("KENN", "Kennesaw State", "CUSA", "Southeast", 118, 2.7, 6.5, 3.1),
    TeamSeed("MUR", "Murray State", "MVC", "South", 105, 4.9, 5.5, 2.6),
    TeamSeed("ODU", "Old Dominion", "Sun Belt", "Mid-Atlantic", 112, 3.7, 5.5, 2.4),
    TeamSeed("TROY", "Troy", "Sun Belt", "South", 116, 2.9, 6.0, 2.7),
    TeamSeed("ECU", "East Carolina", "AAC", "Southeast", 124, 1.3, 6.0, 2.4),
    TeamSeed("GSU", "Georgia State", "Sun Belt", "Southeast", 128, 0.7, 6.5, 2.5),
    TeamSeed("MER", "Mercer", "SoCon", "Southeast", 150, -3.0, 7.0, 2.3),
    TeamSeed("WCU", "Western Carolina", "SoCon", "Southeast", 157, -4.2, 7.0, 2.0),
    TeamSeed("KENN2", "Queens", "ASUN", "Southeast", 171, -6.0, 7.0, 2.4),
    TeamSeed("SCST", "South Carolina State", "MEAC", "Southeast", 229, -12.0, 9.0, 1.1),
    TeamSeed("ALCN", "Alcorn State", "SWAC", "South", 248, -14.8, 10.0, 1.4),
    TeamSeed("FAMU", "Florida A&M", "SWAC", "Southeast", 267, -17.0, 10.0, 1.0),
]


def build_mock_seasons(seasons: list[int]) -> dict[int, list[dict]]:
    data: dict[int, list[dict]] = {}
    for season in seasons:
        rng = Random(season * 97)
        season_rows: list[dict] = []
        for index, seed in enumerate(TEAM_SEEDS):
            season_shift = (season - 2020) * rng.uniform(-0.6, 0.6)
            early_rank = max(1, seed.base_rank + rng.randint(-14, 14) + season_shift)
            trajectory = seed.growth + rng.uniform(-4.5, 4.5)
            late_rank = max(1, early_rank - trajectory + rng.uniform(-3.5, 3.5))
            volatility = max(1.5, seed.volatility + rng.uniform(-1.5, 2.2))
            rank_trajectory: list[float] = []
            for week in range(10):
                progress = week / 9 if week else 0
                baseline = early_rank - (early_rank - late_rank) * progress
                noise = rng.uniform(-volatility, volatility)
                rank_trajectory.append(round(max(1, baseline + noise), 1))
            rank_trajectory[-1] = round(late_rank, 1)
            projected_end_rank = round((rank_trajectory[2] * 0.55) + (rank_trajectory[-1] * 0.45), 1)
            adj_em = round(seed.base_em + rng.uniform(-4.2, 4.2) + (50 - late_rank) / 12, 2)
            adj_o = round(98 + max(adj_em, -10) * 0.72 + rng.uniform(-4.5, 4.5), 2)
            adj_d = round(100 - max(adj_em, -10) * 0.45 + rng.uniform(-4.0, 4.0), 2)
            season_rows.append(
                {
                    "season": season,
                    "team_id": seed.team_id,
                    "team_name": seed.team_name,
                    "conference": seed.conference,
                    "region": seed.region,
                    "early_rank": round(early_rank, 1),
                    "projected_end_rank": round(projected_end_rank, 1),
                    "actual_end_rank": round(late_rank, 1),
                    "trajectory_score": round(early_rank - late_rank, 1),
                    "volatility_score": round(volatility, 2),
                    "adj_em": adj_em,
                    "adj_o": adj_o,
                    "adj_d": adj_d,
                    "rank_trajectory": rank_trajectory,
                    "metadata": {
                        "schedule_strength_bucket": "high" if index < 20 else "mid" if index < 45 else "low",
                        "seed_index": index,
                    },
                }
            )
        data[season] = sorted(season_rows, key=lambda row: row["actual_end_rank"])
    return data

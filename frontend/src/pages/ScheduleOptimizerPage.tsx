import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ScheduleSummary } from "../lib/types";

interface ScheduleOptimizerProps {
  schedule: ScheduleSummary | null;
  loading: boolean;
  onGenerate: () => void;
}

export function ScheduleOptimizerPage({ schedule, loading, onGenerate }: ScheduleOptimizerProps) {
  const quadrantBars = schedule
    ? ["Q1", "Q2", "Q3", "Q4"].map((quadrant) => ({
        quadrant,
        wins: Number(
          schedule.games
            .filter((game) => game.expected_quadrant === quadrant)
            .reduce((total, game) => total + game.win_probability, 0)
            .toFixed(2),
        ),
        losses: Number(
          schedule.games
            .filter((game) => game.expected_quadrant === quadrant)
            .reduce((total, game) => total + (1 - game.win_probability), 0)
            .toFixed(2),
        ),
      }))
    : [];

  return (
    <div className="page-grid">
      <section className="panel action-panel">
        <div>
          <p className="eyebrow">Deterministic search</p>
          <h2>Generate optimal schedule</h2>
          <p>Greedy selection plus local swap search, with home/away caps and duplicate-opponent avoidance.</p>
        </div>
        <button type="button" className="primary-button" onClick={onGenerate} disabled={loading}>
          {loading ? "Generating..." : "Generate Optimal Schedule"}
        </button>
      </section>

      {schedule ? (
        <>
          <section className="panel chart-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Expected results</p>
                <h2>Quadrant wins and losses</h2>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={quadrantBars}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="quadrant" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="wins" fill="#0f5a46" radius={[6, 6, 0, 0]} />
                <Bar dataKey="losses" fill="#cb6e53" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Recommended slate</p>
                <h2>{schedule.games.length} games, score {schedule.expected_resume_score.toFixed(2)}</h2>
              </div>
            </div>
            <div className="schedule-list">
              {schedule.games.map((game) => (
                <article key={`${game.opponent_team_id}-${game.location}`} className="schedule-card">
                  <div>
                    <strong>{game.opponent_name}</strong>
                    <span>{game.location.toUpperCase()} • {game.expected_quadrant} • projected rank {game.projected_end_rank.toFixed(0)}</span>
                  </div>
                  <div>
                    <strong>{(game.expected_resume_value).toFixed(2)}</strong>
                    <span>resume value</span>
                  </div>
                  <p>{game.rationale}</p>
                  <div className="sensitivity-row">
                    {game.sensitivity.map((scenario) => (
                      <span key={scenario.label}>
                        {scenario.label}: {scenario.resume_score.toFixed(2)}
                      </span>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </section>
        </>
      ) : (
        <section className="panel">Generate a schedule to inspect recommendations and sensitivity.</section>
      )}
    </div>
  );
}


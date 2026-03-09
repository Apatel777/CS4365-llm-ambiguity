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
import { MetricCard } from "../components/MetricCard";
import type { OverviewResponse } from "../lib/types";

interface OverviewPageProps {
  overview: OverviewResponse | null;
  loading: boolean;
}

export function OverviewPage({ overview, loading }: OverviewPageProps) {
  if (loading) {
    return <section className="panel">Loading overview...</section>;
  }

  if (!overview) {
    return <section className="panel">Overview data unavailable.</section>;
  }

  const chartData = overview.top_recommendations.map((game) => ({
    opponent: game.opponent_name,
    winProbability: Number((game.win_probability * 100).toFixed(1)),
    resumeValue: game.expected_resume_value,
  }));

  return (
    <div className="page-grid">
      <section className="metrics-grid">
        <MetricCard label="Expected Q1 wins" value={overview.expected_q1_wins.toFixed(2)} hint="Higher is better for at-large leverage" />
        <MetricCard label="Expected Q2 wins" value={overview.expected_q2_wins.toFixed(2)} hint="Secondary resume support" />
        <MetricCard label="Expected bad losses" value={overview.expected_bad_losses.toFixed(2)} hint="Projected Q3/Q4 losses" />
        <MetricCard label="Resume score" value={overview.expected_resume_score.toFixed(2)} hint={`${overview.preset} preset`} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Recommended core slate</p>
            <h2>Top games in baseline schedule</h2>
          </div>
        </div>
        <div className="schedule-list">
          {overview.top_recommendations.map((game) => (
            <article key={`${game.opponent_team_id}-${game.location}`} className="schedule-card">
              <div>
                <strong>{game.opponent_name}</strong>
                <span>{game.location.toUpperCase()} • {game.expected_quadrant}</span>
              </div>
              <div>
                <strong>{(game.win_probability * 100).toFixed(0)}%</strong>
                <span>win probability</span>
              </div>
              <p>{game.rationale}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel chart-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Schedule balance</p>
            <h2>Win odds vs resume value</h2>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#cfd6d1" />
            <XAxis dataKey="opponent" tick={{ fill: "#22362b", fontSize: 12 }} />
            <YAxis yAxisId="left" tick={{ fill: "#22362b" }} />
            <YAxis yAxisId="right" orientation="right" tick={{ fill: "#22362b" }} />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="winProbability" name="Win probability %" fill="#103e2f" radius={[6, 6, 0, 0]} />
            <Bar yAxisId="right" dataKey="resumeValue" name="Resume value" fill="#d9b95b" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </section>
    </div>
  );
}


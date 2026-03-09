import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { BacktestResponse } from "../lib/types";

interface TrendsPageProps {
  backtests: BacktestResponse | null;
  loading: boolean;
}

export function TrendsPage({ backtests, loading }: TrendsPageProps) {
  if (loading) {
    return <section className="panel">Loading backtests...</section>;
  }

  if (!backtests) {
    return <section className="panel">Backtest data unavailable.</section>;
  }

  return (
    <div className="page-grid">
      <section className="panel chart-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Backtest score</p>
            <h2>Optimizer vs random baseline</h2>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={backtests.points}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="season" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="strategy_score" stroke="#0e6251" strokeWidth={3} />
            <Line type="monotone" dataKey="random_score" stroke="#c17b34" strokeWidth={3} />
          </LineChart>
        </ResponsiveContainer>
      </section>

      <section className="panel chart-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Distribution</p>
            <h2>Score gap by season</h2>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={backtests.histogram}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="season" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="score_gap" fill="#103e2f" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </section>
    </div>
  );
}


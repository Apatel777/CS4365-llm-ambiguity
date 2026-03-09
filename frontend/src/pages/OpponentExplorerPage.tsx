import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CandidateRow, Location } from "../lib/types";

interface OpponentExplorerProps {
  candidates: CandidateRow[];
  loading: boolean;
  conference: string;
  conferences: string[];
  location: Location;
  onConferenceChange: (value: string) => void;
  onLocationChange: (value: Location) => void;
}

export function OpponentExplorerPage({
  candidates,
  loading,
  conference,
  conferences,
  location,
  onConferenceChange,
  onLocationChange,
}: OpponentExplorerProps) {
  const selectedTeams = candidates.slice(0, 3);
  const trajectoryData = selectedTeams.flatMap((team) =>
    team.rank_trajectory.map((rank, index) => ({
      week: `W${index + 1}`,
      rank,
      team: team.team_name,
    })),
  );

  return (
    <div className="page-grid">
      <section className="panel controls-grid compact">
        <label>
          <span>Conference</span>
          <select value={conference} onChange={(event) => onConferenceChange(event.target.value)}>
            <option value="">All</option>
            {conferences.map((entry) => (
              <option key={entry} value={entry}>
                {entry}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Location lens</span>
          <select value={location} onChange={(event) => onLocationChange(event.target.value as Location)}>
            <option value="home">Home</option>
            <option value="away">Away</option>
            <option value="neutral">Neutral</option>
          </select>
        </label>
      </section>

      <section className="panel chart-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Candidate landscape</p>
            <h2>Win probability vs projected end rank</h2>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={320}>
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#d7ddd8" />
            <XAxis type="number" dataKey="projected_end_rank" name="Projected end rank" reversed />
            <YAxis
              type="number"
              dataKey={location === "home" ? "win_probability_home" : location === "away" ? "win_probability_away" : "win_probability_neutral"}
              name="Win probability"
              domain={[0, 1]}
            />
            <Tooltip cursor={{ strokeDasharray: "3 3" }} formatter={(value: number) => value.toFixed(2)} />
            <Scatter data={candidates} fill="#0e6251" />
          </ScatterChart>
        </ResponsiveContainer>
      </section>

      <section className="panel chart-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Trajectory view</p>
            <h2>Selected team rank paths</h2>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={trajectoryData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#d7ddd8" />
            <XAxis dataKey="week" />
            <YAxis reversed />
            <Tooltip />
            {selectedTeams.map((team, index) => (
              <Line
                key={team.team_id}
                dataKey="rank"
                data={trajectoryData.filter((point) => point.team === team.team_name)}
                name={team.team_name}
                stroke={["#103e2f", "#d9b95b", "#3d7f6f"][index]}
                strokeWidth={3}
                dot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Explorer table</p>
            <h2>Best opponent candidates</h2>
          </div>
        </div>
        {loading ? (
          <p>Loading candidates...</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Team</th>
                  <th>Conf</th>
                  <th>Proj rank</th>
                  <th>Trajectory</th>
                  <th>Home WP</th>
                  <th>Away WP</th>
                  <th>Neutral WP</th>
                  <th>Quad H/A/N</th>
                  <th>Resume value</th>
                </tr>
              </thead>
              <tbody>
                {candidates.slice(0, 24).map((team) => (
                  <tr key={team.team_id}>
                    <td>{team.team_name}</td>
                    <td>{team.conference}</td>
                    <td>{team.projected_end_rank.toFixed(0)}</td>
                    <td>{team.trajectory_score.toFixed(1)}</td>
                    <td>{(team.win_probability_home * 100).toFixed(0)}%</td>
                    <td>{(team.win_probability_away * 100).toFixed(0)}%</td>
                    <td>{(team.win_probability_neutral * 100).toFixed(0)}%</td>
                    <td>{team.quadrant_home}/{team.quadrant_away}/{team.quadrant_neutral}</td>
                    <td>{team.resume_value.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}


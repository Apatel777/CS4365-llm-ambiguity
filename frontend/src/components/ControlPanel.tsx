import type { RiskPreset } from "../lib/types";

interface ControlPanelProps {
  season: number;
  seasons: number[];
  slots: number;
  maxAway: number;
  minHome: number;
  preset: RiskPreset;
  onSeasonChange: (value: number) => void;
  onSlotsChange: (value: number) => void;
  onMaxAwayChange: (value: number) => void;
  onMinHomeChange: (value: number) => void;
  onPresetChange: (value: RiskPreset) => void;
}

export function ControlPanel(props: ControlPanelProps) {
  return (
    <section className="panel controls-grid">
      <label>
        <span>Season</span>
        <select value={props.season} onChange={(event) => props.onSeasonChange(Number(event.target.value))}>
          {props.seasons.map((season) => (
            <option key={season} value={season}>
              {season}
            </option>
          ))}
        </select>
      </label>
      <label>
        <span>Non-conf slots</span>
        <input type="number" min={1} max={15} value={props.slots} onChange={(event) => props.onSlotsChange(Number(event.target.value))} />
      </label>
      <label>
        <span>Max away</span>
        <input type="number" min={0} max={10} value={props.maxAway} onChange={(event) => props.onMaxAwayChange(Number(event.target.value))} />
      </label>
      <label>
        <span>Min home</span>
        <input type="number" min={0} max={10} value={props.minHome} onChange={(event) => props.onMinHomeChange(Number(event.target.value))} />
      </label>
      <label>
        <span>Risk preset</span>
        <select value={props.preset} onChange={(event) => props.onPresetChange(event.target.value as RiskPreset)}>
          <option value="balanced">Balanced</option>
          <option value="aggressive">Aggressive</option>
          <option value="safe">Safe</option>
        </select>
      </label>
    </section>
  );
}


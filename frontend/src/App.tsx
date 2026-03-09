import { useEffect, useState } from "react";
import { ControlPanel } from "./components/ControlPanel";
import { Sidebar } from "./components/Sidebar";
import {
  fetchBacktests,
  fetchCandidates,
  fetchOverview,
  fetchSeasons,
  fetchTeams,
  optimizeSchedule,
} from "./lib/api";
import type { BacktestResponse, CandidateRow, Location, OverviewResponse, RiskPreset, ScheduleSummary, TeamSummary } from "./lib/types";
import { OpponentExplorerPage } from "./pages/OpponentExplorerPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ScheduleOptimizerPage } from "./pages/ScheduleOptimizerPage";
import { TrendsPage } from "./pages/TrendsPage";

const defaultLockedGame = {
  opponent_team_id: "UGA",
  opponent_name: "Georgia",
  location: "home" as const,
  notes: "Fixed SEC Challenge game",
};

function App() {
  const [activePage, setActivePage] = useState("overview");
  const [seasons, setSeasons] = useState<number[]>([2026]);
  const [teams, setTeams] = useState<TeamSummary[]>([]);
  const [conferenceFilter, setConferenceFilter] = useState("");
  const [locationFilter, setLocationFilter] = useState<Location>("home");
  const [season, setSeason] = useState(2026);
  const [slots, setSlots] = useState(10);
  const [maxAway, setMaxAway] = useState(4);
  const [minHome, setMinHome] = useState(5);
  const [preset, setPreset] = useState<RiskPreset>("balanced");
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [candidates, setCandidates] = useState<CandidateRow[]>([]);
  const [schedule, setSchedule] = useState<ScheduleSummary | null>(null);
  const [backtests, setBacktests] = useState<BacktestResponse | null>(null);
  const [loadingOverview, setLoadingOverview] = useState(false);
  const [loadingCandidates, setLoadingCandidates] = useState(false);
  const [loadingSchedule, setLoadingSchedule] = useState(false);
  const [loadingBacktests, setLoadingBacktests] = useState(false);
  const conferences = Array.from(new Set(teams.map((team) => team.conference))).sort();

  useEffect(() => {
    fetchSeasons()
      .then(setSeasons)
      .catch(() => setSeasons([2026]));
  }, []);

  useEffect(() => {
    fetchTeams(season)
      .then(setTeams)
      .catch(() => setTeams([]));
  }, [season]);

  useEffect(() => {
    setLoadingOverview(true);
    fetchOverview({ season, slots, maxAway, minHome, preset })
      .then(setOverview)
      .catch(() => setOverview(null))
      .finally(() => setLoadingOverview(false));
  }, [season, slots, maxAway, minHome, preset]);

  useEffect(() => {
    setLoadingCandidates(true);
    fetchCandidates({
      season,
      preset,
      conference: conferenceFilter || undefined,
      location: locationFilter,
    })
      .then(setCandidates)
      .catch(() => setCandidates([]))
      .finally(() => setLoadingCandidates(false));
  }, [season, preset, conferenceFilter, locationFilter]);

  useEffect(() => {
    setLoadingBacktests(true);
    fetchBacktests(preset)
      .then(setBacktests)
      .catch(() => setBacktests(null))
      .finally(() => setLoadingBacktests(false));
  }, [preset]);

  function handleGenerateSchedule() {
    setLoadingSchedule(true);
    optimizeSchedule({
      season,
      slots,
      max_away: maxAway,
      min_home: minHome,
      preset,
      locked_games: [defaultLockedGame],
      conferences: [],
      avoid_far_away: false,
    })
      .then(setSchedule)
      .catch(() => setSchedule(null))
      .finally(() => setLoadingSchedule(false));
  }

  return (
    <div className="app-shell">
      <Sidebar active={activePage} onChange={setActivePage} />
      <main className="main-content">
        <ControlPanel
          season={season}
          seasons={seasons}
          slots={slots}
          maxAway={maxAway}
          minHome={minHome}
          preset={preset}
          onSeasonChange={setSeason}
          onSlotsChange={setSlots}
          onMaxAwayChange={setMaxAway}
          onMinHomeChange={setMinHome}
          onPresetChange={setPreset}
        />

        {activePage === "overview" && <OverviewPage overview={overview} loading={loadingOverview} />}
        {activePage === "explorer" && (
          <OpponentExplorerPage
            candidates={candidates}
            loading={loadingCandidates}
            conference={conferenceFilter}
            conferences={conferences}
            location={locationFilter}
            onConferenceChange={setConferenceFilter}
            onLocationChange={setLocationFilter}
          />
        )}
        {activePage === "optimizer" && (
          <ScheduleOptimizerPage schedule={schedule} loading={loadingSchedule} onGenerate={handleGenerateSchedule} />
        )}
        {activePage === "trends" && <TrendsPage backtests={backtests} loading={loadingBacktests} />}
      </main>
    </div>
  );
}

export default App;

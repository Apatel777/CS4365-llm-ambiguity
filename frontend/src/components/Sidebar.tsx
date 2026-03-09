interface SidebarProps {
  active: string;
  onChange: (page: string) => void;
}

const pages = [
  { id: "overview", label: "Overview" },
  { id: "explorer", label: "Opponent Explorer" },
  { id: "optimizer", label: "Schedule Optimizer" },
  { id: "trends", label: "Trends / Backtests" },
];

export function Sidebar({ active, onChange }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div>
        <p className="eyebrow">Georgia Tech</p>
        <h1>Non-Conference Optimizer</h1>
        <p className="sidebar-copy">
          Optimize for NCAA resume value using Torvik-style efficiency signals, rank trajectories, and quadrant math.
        </p>
      </div>
      <nav className="nav-list">
        {pages.map((page) => (
          <button
            key={page.id}
            type="button"
            className={`nav-button ${active === page.id ? "active" : ""}`}
            onClick={() => onChange(page.id)}
          >
            {page.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}


# Georgia Tech Non-Conference Optimizer

Web app for optimizing Georgia Tech men's basketball non-conference scheduling around NCAA Tournament resume value, using Torvik-style ratings, quadrant thresholds, and historical trajectory priors.

## Repo Layout

```text
backend/   FastAPI API, SQLite cache, feature engineering, optimizer, backtests
frontend/  React + TypeScript + Vite dashboard with Recharts visualizations
data/      Runtime SQLite database created automatically
```

## What It Does

- Ingests season ratings through a thin Torvik client with SQLite caching and rate limiting.
- Ships with seeded mock data for seasons 2020-2026 so the app runs end-to-end without network access.
- Engineers early-rank, projected end-rank, trajectory, volatility, win probability, and expected quadrant outcomes.
- Optimizes a non-conference slate with deterministic greedy selection plus local swap search.
- Backtests the strategy against random schedules over 2020-2025.

## Backend Setup

1. Install `uv` if needed: [uv docs](https://docs.astral.sh/uv/)
2. Create backend environment and install dependencies:

```bash
cd /Users/alokpatel/Documents/New\ project/backend
uv sync
```

3. Optional: copy env defaults and switch off mock mode when you have working Torvik access:

```bash
cp .env.example .env
```

Environment variables:

- `USE_MOCK_DATA=true` keeps the app fully local and seeded.
- `TORVIK_BASE_URL=https://www.barttorvik.com`
- If Torvik later documents an API key flow, add it in `.env` and extend the thin adapter in [`backend/app/services/torvik.py`](/Users/alokpatel/Documents/New project/backend/app/services/torvik.py).

4. Run the backend:

```bash
cd /Users/alokpatel/Documents/New\ project/backend
uv run uvicorn app.main:app --reload --port 8000
```

API base URL: `http://localhost:8000/api`

## Frontend Setup

1. Install frontend dependencies:

```bash
cd /Users/alokpatel/Documents/New\ project/frontend
npm install
```

2. Optional: copy the frontend env file if you want a custom API base URL:

```bash
cp .env.example .env
```

3. Run the frontend:

```bash
cd /Users/alokpatel/Documents/New\ project/frontend
npm run dev
```

Open `http://localhost:5173`.

## Makefile Shortcuts

From repo root:

```bash
make backend
make frontend
```

## API Endpoints

- `GET /api/seasons`
- `GET /api/teams?season=2026`
- `GET /api/team/GT/metrics?season=2026`
- `GET /api/candidates?season=2026&preset=balanced&location=home`
- `POST /api/optimize`
- `GET /api/schedule/{id}`
- `GET /api/overview`
- `GET /api/backtests?preset=balanced`

## Torvik Adapter Notes

- The live client is intentionally thin and caches raw responses in SQLite.
- Since Torvik access formats can change, the app defaults to mock mode and falls back to seeded local data if live parsing fails.
- The adapter lives in [`backend/app/services/torvik.py`](/Users/alokpatel/Documents/New project/backend/app/services/torvik.py) and is structured so endpoint parsing can be updated without touching the rest of the system.

## Defaults

- Current season: `2026`
- Non-conference slots: `10`
- Max away games: `4`
- Min home games: `5`
- Fixed SEC game: Georgia at home in the baseline examples
- Risk presets: `balanced`, `aggressive`, `safe`


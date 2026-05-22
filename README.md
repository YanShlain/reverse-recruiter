# ReverseRecruiter

Personal local tool to search LinkedIn jobs, apply manually via browser tabs, and track your application pipeline.

## Quick start (local dev)

Requires [uv](https://docs.astral.sh/uv/).

### Backend

```bash
uv sync
```

Windows (PowerShell):

```powershell
$env:MOCK_MCP = "true"
$env:DATA_DIR = "data"
uv run uvicorn reverse_recruiter.main:app --reload --port 8000
```

macOS / Linux:

```bash
export MOCK_MCP=true DATA_DIR=data
uv run uvicorn reverse_recruiter.main:app --reload --port 8000
```

API: http://localhost:8000/api/v1/health

### Tests

```bash
uv sync --extra dev
uv run pytest              # all tests
uv run pytest tests/integration  # API integration only
```

Uses `MOCK_MCP=true` and an isolated per-test `DATA_DIR` (see `tests/conftest.py`).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: http://localhost:5173

Set `VITE_API_URL=http://localhost:8000/api/v1` if needed.

### Docker Compose

```bash
docker compose up --build
```

- API: http://localhost:8000
- Frontend: http://localhost:5173
- `MOCK_MCP=true` by default (sample jobs). Set `MOCK_MCP=false` and `MCP_BASE_URL` to your LinkedIn MCP endpoint for live data.

## Architecture

See [plan.md](plan.md) and [docs/original_requirements.md](docs/original_requirements.md).

- **Backend:** FastAPI, 3-tier (API → services → JSON/MCP adapters), managed with **uv**
- **Frontend:** React + Vite + TypeScript
- **Data:** `data/*.json` (gitignored)

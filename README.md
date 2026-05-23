# ReverseRecruiter

Personal local tool to search LinkedIn jobs, apply manually via browser tabs, and track your application pipeline.

**Communication boundaries:** the **frontend** calls only the **backend** REST API (`/api/v1`). The **backend** is the only component that talks to **LinkedIn MCP**. The browser never opens MCP URLs.

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
uv run uvicorn backend.main:app --reload --port 8000
```

macOS / Linux:

```bash
export MOCK_MCP=true DATA_DIR=data
uv run uvicorn backend.main:app --reload --port 8000
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

Set `VITE_API_URL=http://localhost:8000/api/v1` if needed. The dev server proxies `/api` to the backend container hostname `backend:8000` when using Compose.

---

## Docker: full stack (MCP → backend → frontend)

`docker-compose.yml` starts three services **in order**:

1. **linkedin-mcp** — [stickerdaniel/linkedin-mcp-server](https://hub.docker.com/r/stickerdaniel/linkedin-mcp-server) on port 3000
2. **backend** — FastAPI (`backend/` package), waits for MCP to start, calls MCP at `http://linkedin-mcp:3000/mcp`
3. **frontend** — React UI, waits for backend, calls **only** `http://localhost:8000/api/v1` (never MCP)

Every inbound REST call is logged by backend request middleware (`API request` / `API response` lines). Outbound MCP calls are logged in `backend.infrastructure.linkedin_mcp.client`.

### 1. One-time LinkedIn login (on the host)

MCP in Docker has no display; create the browser profile on the host first:

```bash
uvx linkedin-scraper-mcp@latest --login
```

Cookies are stored under `~/.linkedin-mcp/` (Windows: `%USERPROFILE%\.linkedin-mcp\`). Compose mounts this directory into the MCP container.

### 2. Start the stack

**Mock mode (default, no live LinkedIn):** sample jobs; MCP container still starts but the backend does not call it.

```bash
docker compose up --build
```

**Live LinkedIn via MCP:**

```bash
MOCK_MCP=false docker compose up --build
```

On Windows, if `~/.linkedin-mcp` does not expand correctly, set an explicit host path:

```powershell
$env:LINKEDIN_MCP_DATA = "$env:USERPROFILE\.linkedin-mcp"
MOCK_MCP=false docker compose up --build
```

**Windows + Docker browser issue:** the `linkedin-mcp` container may fail to start Chromium on a bind-mounted `%USERPROFILE%\.linkedin-mcp` path (`Operation not permitted`). LinkedIn HTTP works, but `get_my_profile` / `search_jobs` fail. Use host MCP instead (same profile dir, no Docker browser):

```powershell
# Stop compose MCP if it holds port 3000
docker compose stop linkedin-mcp

# Host MCP (keep this terminal open)
uvx linkedin-scraper-mcp@latest --transport streamable-http --host 127.0.0.1 --port 3000 --path /mcp

# Local backend (separate terminal)
$env:MOCK_MCP = "false"
$env:MCP_BASE_URL = "http://127.0.0.1:3000/mcp"
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Point Cursor MCP at the same HTTP endpoint (`http://localhost:3000/mcp`) instead of `docker run` (which spawns extra containers without a stable port).

| URL | Service |
|-----|---------|
| http://localhost:5173 | Frontend (browser → backend API only) |
| http://localhost:8000/api/v1 | Backend REST API |
| http://localhost:3000/mcp | MCP (backend only; not used by the UI) |

### 3. Verify backend ↔ MCP in Docker

Run these from the host while `docker compose up` is running.

**MCP container**

```bash
docker compose ps linkedin-mcp
docker compose logs linkedin-mcp --tail 30
curl -s http://localhost:3000/health
```

Expect HTTP 2xx from `/health`. Connection refused means MCP is not listening on 3000.

**Backend can reach MCP** (set `MOCK_MCP=false` for a real ping)

```bash
curl -s http://localhost:8000/api/v1/health
curl -s http://localhost:8000/api/v1/ready
curl -s -X POST http://localhost:8000/api/v1/session/ensure
```

With live MCP and a valid LinkedIn session:

- `/ready` → `{"status":"ok","mcp":true}`
- `/session/ensure` → profile JSON (`headline`, `skills`, `experience_titles`, `raw`, …)

If `/ready` shows `"mcp":false`, check `docker compose logs backend` for `MCP request failed` or `mcp_unavailable`. Confirm `MCP_BASE_URL` is `http://linkedin-mcp:3000/mcp` (Compose default).

**Backend logs for API traffic**

```bash
docker compose logs backend --tail 50
```

Look for lines such as `API request method=GET path=/api/v1/health` and matching `API response ... status=200`.

### 4. Environment variables (Compose)

| Variable | Default | Purpose |
|----------|---------|---------|
| `MOCK_MCP` | `true` | `false` → backend uses real `McpLinkedInGateway` |
| `MCP_BASE_URL` | `http://linkedin-mcp:3000/mcp` | MCP endpoint **inside** the Compose network |
| `LINKEDIN_MCP_DATA` | `~/.linkedin-mcp` | Host path mounted into the MCP container |
| `DATA_DIR` | `/app/data` | JSON persistence (`./data` volume) |
| `LLM_API_KEY` | empty | Optional LLM scoring when `use_llm=true` |
| `LOG_LEVEL` | `info` | Backend log level |

### 5. Run backend against MCP only (no frontend)

Useful when debugging LinkedIn integration:

```bash
docker compose up --build linkedin-mcp backend
```

Then run the curl checks in step 3.

---

## REST API (`/api/v1`)

Base URL: `http://localhost:8000/api/v1`

All examples use `curl`. On Windows, use `curl.exe` in PowerShell or run from Git Bash. Replace `JOB_ID`, `SAVED_ID`, and `EVENT_ID` with values from responses.

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness (API process up) |
| GET | `/ready` | Readiness; includes MCP ping when not in mock mode |

```bash
curl -s http://localhost:8000/api/v1/health
curl -s http://localhost:8000/api/v1/ready
```

### Session

| Method | Path | Description |
|--------|------|-------------|
| POST | `/session/ensure` | LinkedIn session check via MCP `get_my_profile`; returns profile snapshot |

```bash
curl -s -X POST http://localhost:8000/api/v1/session/ensure
```

### Search

| Method | Path | Description |
|--------|------|-------------|
| POST | `/search/` | Run job search (~25 results, ranked) |
| GET | `/search/saved` | List saved searches |
| POST | `/search/saved` | Save current filter set (+ profile snapshot) |
| POST | `/search/saved/{saved_id}/run` | Re-run a saved search |
| GET | `/search/settings` | UI settings (e.g. LLM toggle) |

**Run search** — body fields mirror MCP `search_jobs` (see [docs/original_requirements.md](docs/original_requirements.md)):

```bash
curl -s -X POST http://localhost:8000/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d "{\"keywords\":\"python developer\",\"location\":\"Remote\",\"easy_apply\":false,\"use_llm\":false}"
```

**List / save / re-run saved searches:**

```bash
curl -s http://localhost:8000/api/v1/search/saved

curl -s -X POST http://localhost:8000/api/v1/search/saved \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Remote Python\",\"filters\":{\"keywords\":\"python\",\"location\":\"Remote\"}}"

curl -s -X POST "http://localhost:8000/api/v1/search/saved/SAVED_ID/run?use_llm=false"
```

**Settings:**

```bash
curl -s http://localhost:8000/api/v1/search/settings
```

### Apply

| Method | Path | Description |
|--------|------|-------------|
| POST | `/apply` | Mark jobs `in_progress`; returns `{ "jobs": [{ "job_id", "url", ... }] }` for opening tabs |

```bash
curl -s -X POST http://localhost:8000/api/v1/apply \
  -H "Content-Type: application/json" \
  -d "{\"job_ids\":[\"1001\",\"1002\"]}"
```

### Pipeline

| Method | Path | Description |
|--------|------|-------------|
| GET | `/pipeline` | List pipeline jobs |
| POST | `/pipeline/confirm` | Confirm apply outcome: `submitted` or `skipped` |
| GET | `/pipeline/{job_id}` | Job details |
| PATCH | `/pipeline/{job_id}` | Update lifecycle / stage / rejected |
| POST | `/pipeline/{job_id}/interviews` | Add interview event |
| PATCH | `/pipeline/{job_id}/interviews/{event_id}` | Update interview |
| DELETE | `/pipeline/{job_id}/interviews/{event_id}` | Remove interview |

**List** (optional query: `lifecycle`, `include_rejected`):

```bash
curl -s "http://localhost:8000/api/v1/pipeline"
curl -s "http://localhost:8000/api/v1/pipeline?lifecycle=submitted&include_rejected=false"
```

**Confirm** after applying in the browser:

```bash
curl -s -X POST http://localhost:8000/api/v1/pipeline/confirm \
  -H "Content-Type: application/json" \
  -d "{\"job_ids\":[\"1001\"],\"action\":\"submitted\"}"
```

`action` must be `submitted` or `skipped`.

**Get / update job:**

```bash
curl -s http://localhost:8000/api/v1/pipeline/JOB_ID

curl -s -X PATCH http://localhost:8000/api/v1/pipeline/JOB_ID \
  -H "Content-Type: application/json" \
  -d "{\"progress_stage\":\"screening\"}"
```

Lifecycle values: `in_progress`, `submitted`, `skipped`, `rejected`. Progress stages: `applied`, `screening`, `interview`, `offer`, `hired`, `withdrawn`.

**Interviews:**

```bash
curl -s -X POST http://localhost:8000/api/v1/pipeline/JOB_ID/interviews \
  -H "Content-Type: application/json" \
  -d "{\"datetime\":\"2026-06-01T14:00:00Z\",\"with_whom\":\"Alex\",\"interview_type\":\"video\",\"notes\":\"Round 1\"}"

curl -s -X PATCH http://localhost:8000/api/v1/pipeline/JOB_ID/interviews/EVENT_ID \
  -H "Content-Type: application/json" \
  -d "{\"notes\":\"Rescheduled\"}"

curl -s -X DELETE http://localhost:8000/api/v1/pipeline/JOB_ID/interviews/EVENT_ID
```

Interview types: `phone`, `video`, `onsite`, `technical`, `behavioral`, `other`.

### Typical curl flow (mock mode)

```bash
curl -s http://localhost:8000/api/v1/health
curl -s -X POST http://localhost:8000/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d "{\"keywords\":\"engineer\",\"use_llm\":false}"
# Use job_id values from the JSON array, then:
curl -s -X POST http://localhost:8000/api/v1/apply \
  -H "Content-Type: application/json" \
  -d "{\"job_ids\":[\"1001\",\"1002\"]}"
curl -s http://localhost:8000/api/v1/pipeline
```

### Errors

Failed requests return JSON such as `{"detail":{"error":"<code>","message":"<text>"}}`. Common codes: `mcp_unavailable` (503 on search/session), `session_expired` (401), `not_found` (404).

---

## Architecture

See [plan.md](plan.md) and [docs/original_requirements.md](docs/original_requirements.md).

- **Backend:** FastAPI, 3-tier (API → services → JSON/MCP adapters), managed with **uv**
- **Frontend:** React + Vite + TypeScript
- **Data:** `data/*.json` (gitignored)

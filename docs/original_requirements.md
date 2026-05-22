# Requirements: ReverseRecruiter

**Status:** LOCKED
**Last updated:** 2026-05-22
**Locked:** 2026-05-22 (user confirmed)
**Owner:** User (personal local tool)
**Confidence:** ~96% — product decisions merged; 3 low-risk items deferred to design/spike

---

## 1. Summary

ReverseRecruiter is a **personal, local-only** web application that helps one user find LinkedIn jobs matching their profile, review results in a table, open jobs to apply manually on LinkedIn, and **track the full application pipeline** (submitted, skipped, rejected, interview timeline) in JSON files on disk.

A **Python backend** is the **only** component that talks to the **LinkedIn MCP** (search, profile, job details); the **frontend** talks only to the backend via **REST JSON on localhost** and **opens LinkedIn job URLs in browser tabs** on Apply (URLs from backend). **docker-compose** starts frontend, Python API, and **LinkedIn MCP** for v1.

**Not in v1:** multi-user/cloud hosting, automated Easy Apply submit, scheduled/automatic searches, email/push alerts, PDF/Excel export.

---

## 2. Problem & goals

### Problem statement

Manual LinkedIn job hunting is slow, and it is difficult to track where each application stands (applied, interviewing, rejected) across many companies and roles.

### Success metrics

| Metric | Target | How measured |
|--------|--------|--------------|
| Time saved | Less time finding relevant jobs vs manual LinkedIn browsing | Subjective comparison per search session |
| Pipeline clarity | All active applications have status, stage, and interview-event notes in one place | Zero “lost” in-progress jobs after restart |

### Non-goals (out of scope for v1)

- Multi-user accounts or cloud/SaaS deployment
- Automated Easy Apply submission inside the app
- Scheduled or background job searches without user action
- Email or push notifications for new jobs
- Export of results to PDF or Excel
- Official LinkedIn Partner API integration (use dedicated MCP instead)

---

## 3. Users & context

| Persona / actor | Need | Notes |
|-----------------|------|-------|
| Job seeker (single user) | Search, rank, apply on LinkedIn, track pipeline | Personal machine only |

### Constraints

- LinkedIn access via **dedicated LinkedIn MCP service** (browser/session-based)
- **Manual apply** on LinkedIn: backend returns job URLs; **frontend** opens tabs (batched if blocked); user completes application on LinkedIn
- **Full frontend/backend separation**; backend **must be Python**
- Data stored locally as **JSON files**
- LinkedIn Terms of Service / automation risk accepted for personal local use

---

## 4. Functional requirements

### 4.1 Core flows

| ID | Flow | Description |
|----|------|-------------|
| F-1 | Search & discover | User runs search with MCP filters; backend returns ~25 jobs, match score (rules default, optional LLM), sorted table |
| F-2 | Apply (manual) | User selects jobs → Apply → frontend opens one tab per job URL from backend; jobs marked **In progress**; popup-blocked → batches of 5 |
| F-3 | Review queue | User confirms In progress jobs as **Submitted** or **Skipped**; **submitted_at** set on Submitted confirm |
| F-4 | Pipeline tracking | Search + Pipeline screens; progress stages, interview timeline, rejected filter, split details panel |

#### F-1 Search & discover

1. User starts LinkedIn session via MCP once per session; reuse until session expires.
2. User runs search from **Search** screen with **all MCP filters**: keywords, location, date posted, job type, experience, work type, Easy Apply only, sort.
3. Backend loads **~25 jobs** (1 page / `max_pages=1`), fetches job details via MCP, pulls user profile via `get_my_profile`, computes match score (**rules-based default**; user may enable **optional LLM** scoring via UI toggle), **sorts by score** (no hide-by-threshold).
4. **Saved searches (minimal v1):** user can **save**, **list**, and **run** saved filter sets from the Search screen (no rename/delete in v1). Each saved search stores filters plus a **frozen profile snapshot** used for match scoring on re-run (no re-fetch of `get_my_profile` for scoring on re-run).
5. Re-running a saved search: rows with a **pipeline lifecycle status** (`in_progress`, `submitted`, `skipped`, or `rejected`) appear **dimmed with status badge**; jobs with no pipeline status render normally.

**Results table columns (v1):**

| Column | Required | Notes |
|--------|----------|-------|
| Company | Yes | |
| Position | Yes | Link to job description; click opens details panel |
| Published | Yes | Display exactly as LinkedIn shows (no conversion) |
| Applicant count | Nice-to-have | Blank if unavailable |
| Match score | Yes | Rules-based or LLM (user toggle); profile vs job per scoring mode |
| Location | Yes | |
| Work type | Yes | Remote / hybrid / on-site |
| Salary | Yes | Show `—` when missing |
| Job URL | Yes | |

#### F-2 Apply (manual on LinkedIn)

1. User selects one or more rows → **Apply**.
2. Backend returns job URLs (from MCP-fetched job data); **frontend** opens **one browser tab per job**.
3. If browser blocks popups: frontend opens in **batches of 5** with user prompt between batches.
4. Each job in the Apply action → status **In progress** in local JSON store.

#### F-3 Review queue → Submitted / Skipped

1. **Review queue** lists all **In progress** jobs.
2. User bulk-confirms **Submitted** or **Skipped**.
3. **Submitted** records **`submitted_at`** (applied-at timestamp) at confirm time.
4. User may transition to **Submitted**, **Skipped**, or **Rejected** from **any** prior state (including recovery from mistaken skip).

#### F-4 Pipeline tracking

**Navigation:**

- **Search** — active job hunt and results table
- **Pipeline** — sub-filters: In progress, Submitted, Skipped, Rejected

**Lifecycle states:**

| State | Meaning |
|-------|---------|
| `in_progress` | User clicked Apply; LinkedIn tab opened |
| `submitted` | User confirmed application was sent |
| `skipped` | User never applied to the position (did not pursue) |
| `rejected` | Application closed as rejected; shown as **badge/filter under Submitted area** (no separate top-level Rejected tab) |

**Progress stage** (one current stage per job; **editable at any time** regardless of lifecycle state):

Applied → Screening → Interview → Offer → Hired, plus **Withdrawn**.

| Stage | Meaning |
|-------|---------|
| Withdrawn | User started the application process, then withdrew (distinct from **skipped**, which means never applied) |
| (other stages) | Standard pipeline progression after apply/submit |

**Interviews (per job):**

- Unlimited timeline of interview events
- Each event: datetime, with whom, interview type, notes
- User can add, edit, and delete events

**Details panel:**

- Trigger: click **position name** (not company name alone)
- Shows: job/company info, current progress stage, interview timeline (no separate job-level notes field in v1)
- Layout: **recommended** table top ~60%, details bottom ~40% (final layout at design time)
- Empty state: “Select a position to view application details.”
- Storage remains **per job** (`job_id`); panel may show read-only hint if multiple jobs exist at same company

**LinkedIn already-applied:**

- If `get_job_details` exposes an already-applied indicator → show badge on row
- Otherwise → rely on local status only (spike during design)

### 4.2 States & rules

```mermaid
stateDiagram-v2
  [*] --> new: Search result
  new --> in_progress: Apply opens tab
  in_progress --> submitted: Review queue confirm
  in_progress --> skipped: Review queue confirm
  submitted --> rejected: User marks rejected
  skipped --> submitted: User corrects state
  submitted --> submitted: Update progress or interviews
  rejected --> submitted: User corrects state
```

| Rule | Behavior |
|------|----------|
| Match scoring | Rules-based default; optional LLM toggle; sort all results by score |
| Re-search dimming | Dim + badge only for jobs with pipeline lifecycle status |
| Saved search profile | Frozen snapshot at save time; used for scoring on re-run |
| Saved searches v1 | Save, list, run only (Search screen) |
| Progress stage | Editable anytime; Withdrawn ≠ skipped (see F-4) |
| Rejected UI | Filter/badge within Submitted area |
| Timestamps | `submitted_at` only when user confirms Submitted (not on Apply click) |

### 4.3 Permissions & authorization

| Actor | Action | Allowed? | On deny |
|-------|--------|----------|---------|
| Local user | All app features | Yes | N/A — single user, localhost v1 |

v1: No authentication between frontend and backend (localhost only).

### 4.4 Data

| Data | Source | Retention | PII? |
|------|--------|-----------|------|
| Job search results | LinkedIn MCP | Snapshot per search in JSON | Low |
| User LinkedIn profile | MCP `get_my_profile` | Live fetch for new searches; **frozen snapshot** stored per saved search | Yes |
| Application pipeline | User input | JSON files, indefinite local | Yes |
| Interview notes | User input | Per job in JSON | Possibly |
| Saved searches | User input | JSON | No |

**Persistence:** JSON file(s) in a project data directory (exact paths/names in design).

---

## 5. Architecture boundary (requirements-level)

```mermaid
flowchart LR
  subgraph client [Browser]
    FE[Frontend SPA]
    Tabs[User tabs for Apply]
  end
  subgraph compose [docker-compose v1]
    BE[Python REST API]
    MCP[LinkedIn MCP]
  end
  JSON[(JSON files)]
  LinkedIn[LinkedIn via MCP browser session]
  FE -->|HTTP REST JSON| BE
  FE -->|window.open job URLs| Tabs
  Tabs --> LinkedIn
  BE -->|MCP protocol| MCP
  MCP --> LinkedIn
  BE --> JSON
```

| Rule | Requirement |
|------|-------------|
| MCP access | Backend only for LinkedIn MCP — frontend never calls MCP |
| API style | REST JSON over HTTP on localhost |
| Backend language | Python |
| Frontend stack | No preference — recommend at design (default candidate: React + Vite) |
| Run model | **docker-compose** starts frontend, Python API, and **LinkedIn MCP** |
| Apply mechanism | Backend returns job URLs; **frontend** opens tabs; user applies manually on LinkedIn |

---

## 6. Non-functional requirements

### 6.1 Scalability

| Dimension | Now | 12-month expectation | Implication |
|-----------|-----|----------------------|-------------|
| Users | 1 | 1 | No multi-tenant |
| Jobs per search | ~25 | ~25 | Single MCP page |
| Data volume | Small JSON files | Moderate history | File-based OK |

### 6.2 Resilience

| Dependency | Failure mode | Required behavior |
|------------|--------------|-------------------|
| LinkedIn MCP | Down / error | Clear API error in UI; no silent failure |
| LinkedIn session | Expired | Prompt user to re-authenticate via MCP |
| MCP search | Partial results | Show results with warning |
| Browser popups | Blocked | Fallback: open tabs in batches of 5 |

**Idempotency:** Re-running same saved search is safe; merges with local job status.

**Degraded mode:** If MCP unavailable, Search disabled; Pipeline/history still readable from JSON.

### 6.3 Consistency

| Operation | Consistency need | User-visible guarantee | Conflict handling |
|-----------|------------------|------------------------|-------------------|
| Local JSON writes | Strong | Saved data visible after restart | Last-write-wins |
| LinkedIn search | Eventual | Results reflect time of search | New search replaces result set for that run |

### 6.4 Other NFRs

- **Security:** Bind to localhost; no remote access v1; MCP session is trust boundary
- **Observability:** Backend logs MCP calls and errors (detail at design)
- **Accessibility / i18n:** Not required v1

---

## 7. Scenarios & acceptance criteria

### 7.1 Happy path

| ID | Trigger | Steps | Expected result | Acceptance |
|----|---------|-------|-----------------|------------|
| S-1 | Run search | Profile via MCP, 25 jobs, rank | Table with all columns | Renders within 60s or shows progress/error |
| S-2 | Apply 12 jobs | Select → Apply | FE opens 12 tabs or batched by 5 | All 12 marked `in_progress` |
| S-10 | Saved search re-run | Run saved search with frozen profile | Scores use snapshot; pipeline jobs dimmed | Badge only on jobs with lifecycle status |
| S-11 | LLM match toggle | Enable LLM, run search | Scores from LLM path | Toggle persists per session or app setting (design) |
| S-3 | Review queue | Confirm 3 submitted | `submitted_at` set | Visible under Pipeline → Submitted |
| S-5 | Interview timeline | Add 2 events on one job | Timeline in details panel | Persists after restart |
| S-6 | Details panel | Click position name | Bottom panel shows stage + interviews | Updates when row changes |

### 7.2 Failure & edge cases

| ID | Trigger | Expected result | Acceptance |
|----|---------|-----------------|------------|
| S-4 | Mark submitted as rejected | Rejected badge/filter | Visible under Submitted with Rejected filter |
| S-7 | MCP session expired | Search fails gracefully | User prompted to re-login |
| S-8 | App restart | Reload JSON | Saved searches and all job states unchanged |
| S-9 | Popup blocker | Apply many jobs | Batch of 5 with user continue prompt |

### 7.3 Abuse / misuse

Not applicable for v1 (single-user localhost).

---

## 8. Decisions log

| Date | Decision | Rationale | Decided by |
|------|----------|-----------|------------|
| 2026-05-22 | Personal local tool only | Single user scope | User |
| 2026-05-22 | LinkedIn via dedicated MCP | User requirement | User |
| 2026-05-22 | Manual apply via opened tabs | Superseded — see 2026-05-22 Apply via FE | User |
| 2026-05-22 | Apply via frontend tab open (1B) | MCP has no open-URL tool; BE returns URLs, FE opens tabs | User |
| 2026-05-22 | No job-level notes field | Interview events only; per-interview notes | User |
| 2026-05-22 | Saved searches minimal | Save, list, run on Search screen only | User |
| 2026-05-22 | Frozen profile on saved search | Consistent re-run scoring; no profile re-fetch for score | User |
| 2026-05-22 | Dim jobs with pipeline status only | “Known” = has lifecycle status, not every seen job_id | User |
| 2026-05-22 | Progress stage always editable | Includes skipped/rejected jobs | User |
| 2026-05-22 | Skipped vs Withdrawn | Skipped = never applied; Withdrawn = started then withdrew | User |
| 2026-05-22 | Optional LLM match toggle | Rules default; LLM when enabled | User |
| 2026-05-22 | LinkedIn MCP in docker-compose | One-command stack with FE + API + MCP | User |
| 2026-05-22 | Python backend + REST JSON FE | Full separation | User |
| 2026-05-22 | Backend-only MCP access | Clear security boundary | User |
| 2026-05-22 | docker-compose local run | One command startup | User |
| 2026-05-22 | JSON file persistence | User preference over SQLite | User |
| 2026-05-22 | Rules-based match from profile | Default; optional LLM toggle in v1 | User |
| 2026-05-22 | ~25 jobs per search | Speed vs coverage | User |
| 2026-05-22 | Search + Pipeline navigation | Pipeline sub-filters for statuses | User |
| 2026-05-22 | Rejected under Submitted filter | Not separate top tab | User |
| 2026-05-22 | Interview timeline per job | Full pipeline tracking | User |
| 2026-05-22 | `submitted_at` on confirm Submitted | Applied-at semantics | User |
| 2026-05-22 | Details on position click | User preference | User |
| 2026-05-22 | Bottom split panel recommended | Desktop-local UX | Agent recommend; user deferred layout |

---

## 9. Assumptions

| ID | Assumption | Risk if wrong | Validate by |
|----|------------|---------------|-------------|
| A-1 | ~~MCP opens job URLs~~ | N/A — resolved: FE opens URLs from BE | — |
| A-2 | `get_my_profile` sufficient for rules matching | Poor match quality | Spike + sample profiles |
| A-3 | Salary and applicant count sometimes absent | Empty/`—` cells | `get_job_details` spike |
| A-4 | Personal local use acceptable for MCP automation | Account restriction | User accepts risk |

---

## 10. Open issues

| ID | Issue | Severity | Owner | Target |
|----|-------|----------|-------|--------|
| O-1 | Does `get_job_details` expose “already applied”? | Low | Design | MCP spike |
| O-2 | Exact rules for match score | Low | Design | Design doc |
| O-3 | Frontend framework | Low | Design | Recommend React + Vite |
| O-10 | Review queue entry point (dedicated nav vs Pipeline → In progress only) | Low | Design | Design |
| O-12 | Re-Apply on jobs already `in_progress` / `submitted` | Low | Design | Design |

*Target: zero blockers before LOCKED.*

---

## 11. Confidence breakdown

| Factor | Score (0–100) | Notes |
|--------|---------------|-------|
| Scope & goals | 98 | |
| Functional behavior | 96 | User decisions merged 2026-05-22 |
| NFRs | 90 | MCP in compose; compose startup clarified |
| Scenarios | 94 | S-10, S-11 added |
| Open issues | 92 | 3 low + 2 low deferrals (O-10, O-12) |
| **Weighted total** | **~96%** | Ready for LOCKED pending user confirm |

### Ambiguity review (2026-05-22)

MCP inventory: no `open_job_url` tool — resolved by frontend opening URLs from backend (decision 1B). Session start remains implicit on first MCP call (design-time UX). Remaining deferrals: already-applied badge (O-1), match rules detail (O-2), framework (O-3).

---

## 12. Lock checklist

- [x] Stakeholder reviewed success metrics
- [x] No blocker open issues (3 low-risk deferrals to design/spike)
- [x] NFRs: scalability, resilience, consistency addressed
- [x] Critical scenarios have acceptance criteria
- [x] User confirmed: **requirements LOCKED**

---

## Appendix

### MCP search parameters (reference)

Supported by LinkedIn MCP `search_jobs`: keywords (required), location, date_posted, job_type, experience_level, work_type, easy_apply, sort_by, max_pages (v1 uses 1 page).

### Glossary

- **MCP:** Model Context Protocol service providing LinkedIn browser automation
- **Pipeline:** Application tracking after initial search (In progress → Submitted / Skipped / Rejected)
- **Review queue:** UI to confirm In progress jobs as Submitted or Skipped
- **Skipped:** Never applied to the position
- **Withdrawn (progress stage):** Applied/process started, then user withdrew

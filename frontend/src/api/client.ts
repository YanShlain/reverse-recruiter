/** All UI traffic goes to the Python backend; never call LinkedIn MCP from the browser. */
const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message || err.detail?.message || "Request failed");
  }
  return res.json() as Promise<T>;
}

export interface JobRow {
  job_id: string;
  company: string;
  position: string;
  published: string;
  applicant_count?: string | null;
  match_score?: number | null;
  location: string;
  work_type: string;
  salary?: string | null;
  url: string;
  lifecycle_status?: string | null;
  progress_stage?: string | null;
  already_applied?: boolean | null;
  dimmed?: boolean;
}

export interface PipelineJob extends JobRow {
  submitted_at?: string | null;
  interviews?: InterviewEvent[];
  description?: string;
}

export interface InterviewEvent {
  id: string;
  datetime: string;
  with_whom: string;
  interview_type: string;
  notes: string;
}

export interface SavedSearch {
  id: string;
  name: string;
  filters: Record<string, unknown>;
  created_at: string;
}

export interface ProfileSnapshot {
  headline: string;
  location: string;
  skills: string[];
  experience_titles: string[];
  preferred_work_types: string[];
  raw: Record<string, unknown>;
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  ensureSession: () =>
    request<ProfileSnapshot>("/session/ensure", { method: "POST" }),
  search: (body: Record<string, unknown>) =>
    request<JobRow[]>("/search", { method: "POST", body: JSON.stringify(body) }),
  listSaved: () => request<SavedSearch[]>("/search/saved"),
  saveSearch: (name: string, filters: Record<string, unknown>) =>
    request<SavedSearch>("/search/saved", {
      method: "POST",
      body: JSON.stringify({ name, filters }),
    }),
  runSaved: (id: string, useLlm: boolean) =>
    request<JobRow[]>(`/search/saved/${id}/run?use_llm=${useLlm}`, { method: "POST" }),
  getSettings: () => request<{ use_llm_scoring: boolean }>("/search/settings"),
  apply: (jobIds: string[]) =>
    request<{ jobs: { job_id: string; url: string; dimmed?: boolean }[] }>("/apply", {
      method: "POST",
      body: JSON.stringify({ job_ids: jobIds }),
    }),
  listPipeline: (lifecycle?: string, includeRejected = false) => {
    const params = new URLSearchParams();
    if (lifecycle) params.set("lifecycle", lifecycle);
    if (includeRejected) params.set("include_rejected", "true");
    const q = params.toString();
    return request<PipelineJob[]>(`/pipeline${q ? `?${q}` : ""}`);
  },
  confirm: (jobIds: string[], action: "submitted" | "skipped") =>
    request<PipelineJob[]>("/pipeline/confirm", {
      method: "POST",
      body: JSON.stringify({ job_ids: jobIds, action }),
    }),
  getJob: (jobId: string) => request<PipelineJob>(`/pipeline/${jobId}`),
  updateJob: (jobId: string, patch: Record<string, unknown>) =>
    request<PipelineJob>(`/pipeline/${jobId}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    }),
  addInterview: (jobId: string, body: Record<string, unknown>) =>
    request<PipelineJob>(`/pipeline/${jobId}/interviews`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

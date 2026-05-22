import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, type JobRow } from "../api/client";
import { DetailsPanel } from "../components/DetailsPanel";
import { JobTable } from "../components/JobTable";
import { openJobUrls } from "../utils/applyBatch";

export function SearchPage() {
  const qc = useQueryClient();
  const [keywords, setKeywords] = useState("software engineer");
  const [location, setLocation] = useState("");
  const [useLlm, setUseLlm] = useState(false);
  const [rows, setRows] = useState<JobRow[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [selectedJob, setSelectedJob] = useState<JobRow | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const savedQuery = useQuery({
    queryKey: ["saved"],
    queryFn: api.listSaved,
  });

  const settingsQuery = useQuery({
    queryKey: ["settings"],
    queryFn: api.getSettings,
  });

  const runSearch = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.ensureSession();
      const result = await api.search({
        keywords,
        location: location || null,
        max_pages: 1,
        use_llm: useLlm,
      });
      setRows(result);
      setSelected(new Set());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
    } finally {
      setLoading(false);
    }
  };

  const applyMutation = useMutation({
    mutationFn: async () => {
      const ids = [...selected];
      const res = await api.apply(ids);
      const urls = res.jobs.filter((j) => !j.dimmed).map((j) => j.url);
      await openJobUrls(urls, async (remaining) =>
        window.confirm(`${remaining} tabs remaining. Open next batch of 5?`)
      );
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      runSearch();
    },
  });

  const saveMutation = useMutation({
    mutationFn: () =>
      api.saveSearch(keywords, { keywords, location: location || null, max_pages: 1 }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["saved"] }),
  });

  const handlePositionClick = async (job: JobRow) => {
    setSelectedJob(job);
    try {
      const full = await api.getJob(job.job_id);
      setSelectedJob(full);
    } catch {
      setSelectedJob(job);
    }
  };

  return (
    <div className="page split">
      <div className="main-pane">
        <h1>Search</h1>
        {error && <div className="error">{error}</div>}
        <div className="toolbar">
          <input
            placeholder="Keywords"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
          />
          <input
            placeholder="Location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />
          <label>
            <input
              type="checkbox"
              checked={useLlm || settingsQuery.data?.use_llm_scoring}
              onChange={(e) => setUseLlm(e.target.checked)}
            />
            LLM scoring
          </label>
          <button onClick={runSearch} disabled={loading}>
            {loading ? "Searching…" : "Search"}
          </button>
          <button onClick={() => saveMutation.mutate()}>Save search</button>
          <button
            disabled={selected.size === 0}
            onClick={() => applyMutation.mutate()}
          >
            Apply ({selected.size})
          </button>
        </div>
        {savedQuery.data && savedQuery.data.length > 0 && (
          <div className="saved-list">
            Saved:{" "}
            {savedQuery.data.map((s) => (
              <button
                key={s.id}
                onClick={async () => {
                  setLoading(true);
                  try {
                    const result = await api.runSaved(s.id, useLlm);
                    setRows(result);
                  } catch (e) {
                    setError(e instanceof Error ? e.message : "Run failed");
                  } finally {
                    setLoading(false);
                  }
                }}
              >
                {s.name}
              </button>
            ))}
          </div>
        )}
        <JobTable
          rows={rows}
          selected={selected}
          onSelect={setSelected}
          onPositionClick={handlePositionClick}
        />
      </div>
      <DetailsPanel
        job={selectedJob}
        onUpdated={() => selectedJob && handlePositionClick(selectedJob)}
      />
    </div>
  );
}

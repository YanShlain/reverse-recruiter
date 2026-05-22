import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, type JobRow, type PipelineJob } from "../api/client";
import { DetailsPanel } from "../components/DetailsPanel";
import { JobTable } from "../components/JobTable";
import { openJobUrls } from "../utils/applyBatch";

const FILTERS = [
  { key: "in_progress", label: "In progress" },
  { key: "submitted", label: "Submitted" },
  { key: "skipped", label: "Skipped" },
] as const;

export function PipelinePage() {
  const [params] = useSearchParams();
  const filter = params.get("filter") || "in_progress";
  const includeRejected = params.get("rejected") === "true";
  const qc = useQueryClient();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [selectedJob, setSelectedJob] = useState<PipelineJob | null>(null);

  const query = useQuery({
    queryKey: ["pipeline", filter, includeRejected],
    queryFn: () =>
      api.listPipeline(
        filter === "submitted" ? "submitted" : filter,
        filter === "submitted" && includeRejected
      ),
  });

  const rows: JobRow[] = useMemo(
    () =>
      (query.data || []).map((j) => ({
        ...j,
        salary: j.salary || "—",
        dimmed: false,
      })),
    [query.data]
  );

  const confirmMutation = useMutation({
    mutationFn: (action: "submitted" | "skipped") =>
      api.confirm([...selected], action),
    onSuccess: () => {
      setSelected(new Set());
      qc.invalidateQueries({ queryKey: ["pipeline"] });
    },
  });

  const applyMutation = useMutation({
    mutationFn: async () => {
      const res = await api.apply([...selected]);
      const urls = res.jobs.map((j) => j.url);
      await openJobUrls(urls, async (remaining) =>
        window.confirm(`${remaining} tabs remaining. Open next batch of 5?`)
      );
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pipeline"] }),
  });

  const markRejected = async (jobId: string) => {
    await api.updateJob(jobId, { rejected: true });
    qc.invalidateQueries({ queryKey: ["pipeline"] });
  };

  const handlePositionClick = async (job: JobRow) => {
    const full = await api.getJob(job.job_id);
    setSelectedJob(full);
  };

  return (
    <div className="page split">
      <div className="main-pane">
        <h1>Pipeline</h1>
        <nav className="subnav">
          {FILTERS.map((f) => (
            <Link
              key={f.key}
              to={`/pipeline?filter=${f.key}`}
              className={filter === f.key ? "active" : ""}
            >
              {f.label}
            </Link>
          ))}
          {filter === "submitted" && (
            <Link
              to="/pipeline?filter=submitted&rejected=true"
              className={includeRejected ? "active" : ""}
            >
              Include rejected
            </Link>
          )}
        </nav>
        {filter === "in_progress" && (
          <div className="toolbar review">
            <span>Review queue — confirm after applying on LinkedIn</span>
            <button
              disabled={selected.size === 0}
              onClick={() => confirmMutation.mutate("submitted")}
            >
              Confirm submitted
            </button>
            <button
              disabled={selected.size === 0}
              onClick={() => confirmMutation.mutate("skipped")}
            >
              Confirm skipped
            </button>
            <button
              disabled={selected.size === 0}
              onClick={() => applyMutation.mutate()}
            >
              Re-open URLs
            </button>
          </div>
        )}
        {filter === "submitted" && selectedJob && (
          <button onClick={() => markRejected(selectedJob.job_id)}>
            Mark rejected
          </button>
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

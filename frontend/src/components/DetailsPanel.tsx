import { useState } from "react";
import { api, type PipelineJob } from "../api/client";

interface Props {
  job: PipelineJob | null;
  onUpdated: () => void;
}

const STAGES = ["applied", "screening", "interview", "offer", "hired", "withdrawn"];

export function DetailsPanel({ job, onUpdated }: Props) {
  const [notes, setNotes] = useState("");
  const [withWhom, setWithWhom] = useState("");
  const [type, setType] = useState("other");

  if (!job) {
    return (
      <div className="details-panel empty">
        Select a position to view application details.
      </div>
    );
  }

  const addInterview = async () => {
    await api.addInterview(job.job_id, {
      datetime: new Date().toISOString(),
      with_whom: withWhom,
      interview_type: type,
      notes,
    });
    setNotes("");
    setWithWhom("");
    onUpdated();
  };

  const updateStage = async (stage: string) => {
    await api.updateJob(job.job_id, { progress_stage: stage });
    onUpdated();
  };

  return (
    <div className="details-panel">
      <h3>
        {job.position} — {job.company}
      </h3>
      <p>
        {job.location} · {job.work_type} · Score {job.match_score?.toFixed(1) ?? "—"}
      </p>
      <label>
        Progress stage{" "}
        <select
          value={job.progress_stage || "applied"}
          onChange={(e) => updateStage(e.target.value)}
        >
          {STAGES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </label>
      <h4>Interview timeline</h4>
      <ul>
        {(job.interviews || []).map((ev) => (
          <li key={ev.id}>
            {new Date(ev.datetime).toLocaleString()} — {ev.interview_type} with{" "}
            {ev.with_whom || "—"}: {ev.notes || "(no notes)"}
          </li>
        ))}
      </ul>
      <div className="interview-form">
        <input
          placeholder="With whom"
          value={withWhom}
          onChange={(e) => setWithWhom(e.target.value)}
        />
        <select value={type} onChange={(e) => setType(e.target.value)}>
          <option value="phone">phone</option>
          <option value="video">video</option>
          <option value="onsite">onsite</option>
          <option value="technical">technical</option>
          <option value="behavioral">behavioral</option>
          <option value="other">other</option>
        </select>
        <input
          placeholder="Notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
        <button onClick={addInterview}>Add event</button>
      </div>
    </div>
  );
}

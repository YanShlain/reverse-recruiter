import type { JobRow } from "../api/client";

interface Props {
  rows: JobRow[];
  selected: Set<string>;
  onSelect: (ids: Set<string>) => void;
  onPositionClick: (job: JobRow) => void;
}

export function JobTable({ rows, selected, onSelect, onPositionClick }: Props) {
  const toggle = (id: string) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onSelect(next);
  };

  const toggleAll = () => {
    if (selected.size === rows.length) onSelect(new Set());
    else onSelect(new Set(rows.map((r) => r.job_id)));
  };

  return (
    <table className="job-table">
      <thead>
        <tr>
          <th>
            <input
              type="checkbox"
              checked={rows.length > 0 && selected.size === rows.length}
              onChange={toggleAll}
            />
          </th>
          <th>Company</th>
          <th>Position</th>
          <th>Published</th>
          <th>Applicants</th>
          <th>Score</th>
          <th>Location</th>
          <th>Work type</th>
          <th>Salary</th>
          <th>Status</th>
          <th>URL</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.job_id} className={row.dimmed ? "dimmed" : ""}>
            <td>
              <input
                type="checkbox"
                checked={selected.has(row.job_id)}
                onChange={() => toggle(row.job_id)}
              />
            </td>
            <td>{row.company}</td>
            <td>
              <button className="link-btn" onClick={() => onPositionClick(row)}>
                {row.position}
              </button>
              {row.already_applied && <span className="badge">Applied on LI</span>}
            </td>
            <td>{row.published}</td>
            <td>{row.applicant_count || ""}</td>
            <td>{row.match_score?.toFixed(1) ?? "—"}</td>
            <td>{row.location}</td>
            <td>{row.work_type}</td>
            <td>{row.salary || "—"}</td>
            <td>
              {row.lifecycle_status && (
                <span className="badge">{row.lifecycle_status}</span>
              )}
            </td>
            <td>
              <a href={row.url} target="_blank" rel="noreferrer">
                Open
              </a>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

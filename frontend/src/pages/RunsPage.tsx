import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "../api/client";
import { deleteRun, getRunPdfUrl, listRuns } from "../api/timetables";
import StatusBadge from "../components/StatusBadge";
import type { GenerationRunListItem } from "../types/api";
import { formatDateTime } from "../utils/format";

export default function RunsPage() {
  const [runs, setRuns] = useState<GenerationRunListItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const loadRuns = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await listRuns();
      setRuns(data);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to load runs.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadRuns();
  }, []);

  const handleDelete = async (runId: number) => {
    setError(null);
    setInfo(null);
    setDeletingId(runId);
    try {
      await deleteRun(runId);
      setRuns((prev) => prev.filter((run) => run.id !== runId));
      setInfo(`Run ${runId} deleted.`);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to delete run.";
      setError(message);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <h1>Runs</h1>
          <p>Browse previous generations and download results.</p>
        </div>
      </div>

      {(error || info) && (
        <div className={`panel banner ${error ? "banner-error" : "banner-info"}`}>
          {error || info}
        </div>
      )}

      <div className="panel" style={{ animationDelay: "0.05s" }}>
        <div className="panel-title">Run History</div>
        {isLoading ? (
          <div className="hint">Loading runs…</div>
        ) : runs.length === 0 ? (
          <div className="hint">No runs yet.</div>
        ) : (
          <div className="table">
            <div className="table-header table-runs">
              <span>Run</span>
              <span>Dataset</span>
              <span>Created</span>
              <span>Status</span>
              <span>File</span>
              <span>Actions</span>
            </div>
            {runs.map((run) => {
              const datasetLabel =
                run.dataset_name || (run.dataset_id ? `Dataset ${run.dataset_id}` : "-");
              const canDownload = run.status === "done" && run.has_pdf;
              const fileName = `schedule_${run.id}.pdf`;
              return (
                <div className="table-row table-runs" key={run.id}>
                  <span>{run.id}</span>
                  <span>{datasetLabel}</span>
                  <span>{formatDateTime(run.created_at)}</span>
                  <span>
                    <StatusBadge status={run.status} />
                  </span>
                  <span className={run.has_pdf ? "" : "text-muted"}>{fileName}</span>
                  <span className="row-actions">
                    {run.status === "done" ? (
                      <Link
                        className="button button-secondary"
                        to={`/runs/${run.id}/schedule`}
                      >
                        View Schedule
                      </Link>
                    ) : (
                      <span className="button button-secondary button-disabled">
                        View Schedule
                      </span>
                    )}
                    {canDownload ? (
                      <a
                        className="button button-secondary"
                        href={getRunPdfUrl(run.id)}
                        target="_blank"
                        rel="noreferrer"
                        download
                      >
                        Download
                      </a>
                    ) : (
                      <span className="button button-secondary button-disabled">
                        Download
                      </span>
                    )}
                    <button
                      className="button button-danger"
                      onClick={() => handleDelete(run.id)}
                      disabled={deletingId === run.id}
                    >
                      {deletingId === run.id ? "Deleting..." : "Delete"}
                    </button>
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}

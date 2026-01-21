import { useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { generateTimetable, getRunResult, getRunStatus } from "../api/timetables";
import JsonViewer from "../components/JsonViewer";
import StatusBadge from "../components/StatusBadge";
import type { GenerationRun } from "../types/api";
import { formatDateTime } from "../utils/format";

const POLL_INTERVAL_MS = 1500;

export default function GeneratePage() {
  const [datasetId, setDatasetId] = useState("");
  const [run, setRun] = useState<GenerationRun | null>(null);
  const [result, setResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleGenerate = async () => {
    setError(null);
    setInfo(null);
    setResult(null);
    setRun(null);

    const parsedId = datasetId.trim() ? Number(datasetId.trim()) : undefined;
    if (datasetId.trim() && Number.isNaN(parsedId)) {
      setError("Dataset id must be a number.");
      return;
    }

    try {
      setIsSubmitting(true);
      const response = await generateTimetable(parsedId);
      setRun({
        id: response.run_id,
        status: response.status,
        progress: 0,
        created_at: new Date().toISOString(),
      });
      setInfo("Generation started. Polling status...");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to start run.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    if (!run?.id) {
      return;
    }

    let active = true;
    let intervalId: number | undefined;

    const poll = async () => {
      try {
        const status = await getRunStatus(run.id);
        if (!active) {
          return;
        }
        setRun(status);

        if (status.status === "done") {
          const payload = await getRunResult(run.id);
          if (active) {
            setResult(payload);
            setInfo("Result is ready.");
          }
          if (intervalId) {
            clearInterval(intervalId);
          }
        }

        if (status.status === "failed") {
          setInfo(null);
          if (intervalId) {
            clearInterval(intervalId);
          }
        }
      } catch (err) {
        if (!active) {
          return;
        }
        const apiError = err instanceof ApiError ? err : null;
        if (apiError?.status === 409) {
          setInfo("Result not ready yet.");
          return;
        }
        setError(apiError?.message ?? "Failed to fetch status.");
        if (intervalId) {
          clearInterval(intervalId);
        }
      }
    };

    poll();
    intervalId = window.setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      active = false;
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [run?.id]);

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <h1>Generate timetable</h1>
          <p>Kick off a GA run and watch the progress live.</p>
        </div>
      </div>

      <div className="panel" style={{ animationDelay: "0.05s" }}>
        <div className="panel-title">Run configuration</div>
        <div className="form-grid">
          <label className="field">
            <span>Dataset id (optional)</span>
            <input
              value={datasetId}
              onChange={(event) => setDatasetId(event.target.value)}
              placeholder="Leave empty to use latest dataset"
            />
          </label>
          <button className="primary" onClick={handleGenerate} disabled={isSubmitting}>
            {isSubmitting ? "Starting..." : "Generate timetable"}
          </button>
        </div>
        <div className="hint">If empty, backend uses the most recent Dataset.</div>
      </div>

      {(error || info) && (
        <div className={`panel banner ${error ? "banner-error" : "banner-info"}`}>
          {error || info}
        </div>
      )}

      {run && (
        <div className="panel" style={{ animationDelay: "0.1s" }}>
          <div className="panel-title">Run status</div>
          <div className="status-grid">
            <div>
              <div className="label">Run id</div>
              <div className="value">{run.id}</div>
            </div>
            <div>
              <div className="label">Status</div>
              <StatusBadge status={run.status} />
            </div>
            <div>
              <div className="label">Progress</div>
              <div className="value">{run.progress}%</div>
            </div>
            <div>
              <div className="label">Created</div>
              <div className="value">{formatDateTime(run.created_at)}</div>
            </div>
            <div>
              <div className="label">Started</div>
              <div className="value">{formatDateTime(run.started_at)}</div>
            </div>
            <div>
              <div className="label">Finished</div>
              <div className="value">{formatDateTime(run.finished_at)}</div>
            </div>
          </div>

          {run.status === "failed" && (
            <div className="inline-error">
              {run.error_message || "Run failed. Check backend logs."}
            </div>
          )}
        </div>
      )}

      {run && run.status === "done" && result && (
        <div className="panel" style={{ animationDelay: "0.15s" }}>
          <div className="panel-title">Result payload</div>
          <JsonViewer value={result} />
        </div>
      )}

      {run && run.status === "done" && !result && (
        <div className="panel" style={{ animationDelay: "0.15s" }}>
          <div className="panel-title">Result payload</div>
          <div className="hint">Not ready yet. Polling continues.</div>
        </div>
      )}
    </section>
  );
}

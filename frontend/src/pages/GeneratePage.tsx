import { useEffect, useMemo, useState } from "react";
import { ApiError } from "../api/client";
import {
  deleteRunPdf,
  generateTimetable,
  getRunPdfUrl,
  getRunResult,
  getRunStatus,
} from "../api/timetables";
import ScheduleTable from "../components/ScheduleTable";
import StatusBadge from "../components/StatusBadge";
import type { GenerationRun, ScheduleByDay, TimetableResultPayload } from "../types/api";
import { formatDateTime } from "../utils/format";
import { collectClassNames, collectLessonsForClass, getScheduleDays } from "../utils/schedule";
import { Progress } from "@/components/ui/progress";

const POLL_INTERVAL_MS = 1500;

export default function GeneratePage() {
  const panelClass =
    "rounded-[18px] border border-[var(--border)] bg-[var(--surface)] px-[22px] py-5 shadow-[var(--shadow)] animate-[rise_0.5s_ease_both]";
  const panelTitleClass = "mb-4 text-[0.95rem] font-semibold";
  const hintClass = "text-sm text-[var(--muted)]";
  const labelClass = "text-xs text-[var(--muted)]";
  const valueClass = "font-semibold";
  const primaryButtonClass =
    "inline-flex items-center justify-center rounded-xl bg-[var(--accent)] px-5 py-3 font-semibold text-white shadow-[0_12px_30px_rgba(15,118,110,0.24)] transition hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[rgba(15,118,110,0.5)] disabled:cursor-not-allowed disabled:opacity-65 disabled:shadow-none";
  const secondaryButtonClass =
    "inline-flex min-w-[110px] items-center justify-center rounded-[10px] border border-[var(--border)] bg-white px-3.5 py-2.5 text-sm font-medium text-[var(--text)] shadow-[0_10px_24px_rgba(20,18,12,0.1)] transition hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[rgba(15,118,110,0.4)] disabled:cursor-not-allowed disabled:opacity-60";
  const dangerButtonClass =
    "inline-flex min-w-[110px] items-center justify-center rounded-[10px] border border-[rgba(185,28,28,0.35)] bg-[rgba(185,28,28,0.1)] px-3.5 py-2.5 text-sm font-medium text-[var(--error)] transition hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[rgba(185,28,28,0.4)] disabled:cursor-not-allowed disabled:opacity-60";
  const disabledButtonClass = `${secondaryButtonClass} pointer-events-none`;

  const [datasetId, setDatasetId] = useState("");
  const [generations, setGenerations] = useState("");
  const [lastSubmittedGenerations, setLastSubmittedGenerations] = useState<number | null>(null);
  const [run, setRun] = useState<GenerationRun | null>(null);
  const [result, setResult] = useState<TimetableResultPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [pdfDeleted, setPdfDeleted] = useState(false);

  const schedule = (result?.schedule ?? {}) as ScheduleByDay;
  const days = useMemo(() => getScheduleDays(schedule), [schedule]);
  const classNames = useMemo(() => collectClassNames(schedule), [schedule]);
  const lessonsByClass = useMemo(() => {
    const map: Record<string, string[]> = {};
    for (const className of classNames) {
      map[className] = collectLessonsForClass(schedule, className, days);
    }
    return map;
  }, [classNames, days, schedule]);
  const hasSchedule =
    classNames.length > 0 &&
    classNames.some((className) => (lessonsByClass[className]?.length ?? 0) > 0);

  const formatDuration = (seconds: number) => {
    if (!Number.isFinite(seconds) || seconds < 0) {
      return "-";
    }
    const rounded = Math.round(seconds);
    if (rounded < 60) {
      return `${rounded}s`;
    }
    const minutes = Math.floor(rounded / 60);
    const remainingSeconds = rounded % 60;
    if (minutes < 60) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m`;
  };

  const generationsFromRun = useMemo(() => {
    const params = run?.params as Record<string, unknown> | undefined;
    const rawValue = params?.generations;
    const numericValue =
      typeof rawValue === "number"
        ? rawValue
        : typeof rawValue === "string"
          ? Number(rawValue)
          : undefined;
    if (!Number.isFinite(numericValue) || !numericValue) {
      return null;
    }
    return numericValue;
  }, [run?.params]);

  const generationsDisplay = generationsFromRun ?? lastSubmittedGenerations;
  const generationsValueLabel = generationsDisplay ? `${generationsDisplay}` : "Default (200)";

  const startedAt = run?.started_at ? new Date(run.started_at) : null;
  const finishedAt = run?.finished_at ? new Date(run.finished_at) : null;
  const durationSeconds =
    startedAt && finishedAt ? (finishedAt.getTime() - startedAt.getTime()) / 1000 : null;

  const finishedValue = () => {
    if (!run) {
      return "-";
    }
    if (run.status === "running") {
      return formatDateTime(run.finished_at);
    }
    if (run.status === "done") {
      const finishedLabel = formatDateTime(run.finished_at);
      const durationLabel = durationSeconds ? ` (${formatDuration(durationSeconds)})` : "";
      return `${finishedLabel}${durationLabel}`;
    }
    return formatDateTime(run.finished_at);
  };

  const handleGenerate = async () => {
    setError(null);
    setInfo(null);
    setResult(null);
    setRun(null);
    setPdfDeleted(false);

    const parsedId = datasetId.trim() ? Number(datasetId.trim()) : undefined;
    if (datasetId.trim() && Number.isNaN(parsedId)) {
      setError("Dataset id must be a number.");
      return;
    }
    const generationsValue = generations.trim();
    const parsedGenerations = generationsValue ? Number(generationsValue) : undefined;
    if (
      generationsValue &&
      (parsedGenerations === undefined ||
        !Number.isFinite(parsedGenerations) ||
        !Number.isInteger(parsedGenerations) ||
        parsedGenerations <= 0)
    ) {
      setError("Generations must be a positive integer.");
      return;
    }

    try {
      setIsSubmitting(true);
      setLastSubmittedGenerations(parsedGenerations ?? null);
      const response = await generateTimetable(
        parsedId,
        parsedGenerations ? { generations: parsedGenerations } : undefined,
      );
      setRun({
        id: response.run_id,
        status: response.status,
        progress: 0,
        params: parsedGenerations ? { generations: parsedGenerations } : undefined,
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

  const handleDeletePdf = async () => {
    if (!run?.id) {
      return;
    }
    setError(null);
    setInfo(null);
    setIsDeleting(true);
    try {
      await deleteRunPdf(run.id);
      setPdfDeleted(true);
      setInfo("PDF deleted.");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to delete PDF.";
      setError(message);
    } finally {
      setIsDeleting(false);
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
    <section className="grid gap-6">
      <div className="grid gap-2">
        <div>
          <h1 className="text-3xl font-semibold">Generate timetable</h1>
          <p className="text-muted">Kick off a GA run and watch the progress live.</p>
        </div>
      </div>

      <div className={panelClass} style={{ animationDelay: "0.05s" }}>
        <div className={panelTitleClass}>Run configuration</div>
        <div className="grid gap-4 items-end md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
          <label className="grid gap-2 text-sm">
            <span>Dataset id (optional)</span>
            <input
              className="w-full rounded-xl border border-border bg-(--surface-strong) px-3 py-2 text-sm"
              value={datasetId}
              onChange={(event) => setDatasetId(event.target.value)}
              placeholder="Leave empty to use latest dataset"
            />
          </label>
          <label className="grid gap-2 text-sm">
            <span>Generations (optional)</span>
            <input
              className="w-full rounded-xl border border-border bg-(--surface-strong) px-3 py-2 text-sm"
              type="number"
              min={1}
              step={1}
              value={generations}
              onChange={(event) => setGenerations(event.target.value)}
              placeholder="Default: 200"
            />
          </label>
          <button className={primaryButtonClass} onClick={handleGenerate} disabled={isSubmitting}>
            {isSubmitting ? "Starting..." : "Generate timetable"}
          </button>
        </div>
        <div className={hintClass}>
          Leave fields empty to use the latest dataset and default GA generations (200).
        </div>
      </div>

      {(error || info) && (
        <div
          className={`${panelClass} ${
            error
              ? "border-[rgba(185,28,28,0.3)] bg-[rgba(185,28,28,0.12)]"
              : "border-[rgba(15,118,110,0.3)] bg-[rgba(15,118,110,0.12)]"
          }`}
        >
          {error || info}
        </div>
      )}

      {run && (
        <div className={panelClass} style={{ animationDelay: "0.1s" }}>
          <div className={panelTitleClass}>Run status</div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <div className={labelClass}>Run id</div>
              <div className={valueClass}>{run.id}</div>
            </div>
            <div>
              <div className={labelClass}>Status</div>
              <StatusBadge status={run.status} />
            </div>
            <div>
              <div className={labelClass}>Progress</div>
              <div className={valueClass}>{run.progress}%</div>
              <Progress value={run.progress} className="mt-2 w-full" />
            </div>
            <div>
              <div className={labelClass}>Generations</div>
              <div className={valueClass}>{generationsValueLabel}</div>
            </div>
            <div>
              <div className={labelClass}>Started</div>
              <div className={valueClass}>{formatDateTime(run.started_at)}</div>
            </div>
            <div>
              <div className={labelClass}>Finished</div>
              <div className={valueClass}>{finishedValue()}</div>
            </div>
          </div>

          {run.status === "failed" && (
            <div className="mt-3 font-semibold text-(--error)">
              {run.error_message || "Run failed. Check backend logs."}
            </div>
          )}
        </div>
      )}

      {run && run.status === "done" && result && (
        <div className={panelClass} style={{ animationDelay: "0.15s" }}>
          <div className={panelTitleClass}>Result file</div>
          <div className="flex flex-col gap-4 rounded-2xl border border-border bg-(--surface-strong) p-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="grid gap-1">
              <div className="font-semibold">{`schedule_${run.id}.pdf`}</div>
              <div className="text-sm text-muted">
                Generated: {formatDateTime(run.finished_at || run.created_at)}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {pdfDeleted ? (
                <span className={disabledButtonClass}>Download</span>
              ) : (
                <a
                  className={secondaryButtonClass}
                  href={getRunPdfUrl(run.id)}
                  target="_blank"
                  rel="noreferrer"
                  download
                >
                  Download
                </a>
              )}
              <button
                className={dangerButtonClass}
                onClick={handleDeletePdf}
                disabled={isDeleting || pdfDeleted}
              >
                {pdfDeleted ? "Deleted" : isDeleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
          {pdfDeleted && <div className={hintClass}>PDF has been deleted.</div>}
        </div>
      )}

      {run && run.status === "done" && result && (
        <div className={panelClass} style={{ animationDelay: "0.18s" }}>
          <div className={panelTitleClass}>Schedule preview</div>
          <div className={hintClass}>Per-class timetable for Monday to Friday.</div>
        </div>
      )}

      {run && run.status === "done" && result && hasSchedule && (
        <div className="grid gap-5" style={{ animationDelay: "0.2s" }}>
          {classNames.map((className) => (
            <ScheduleTable
              key={className}
              classLabel={className}
              days={days}
              lessons={lessonsByClass[className] ?? []}
              schedule={schedule}
            />
          ))}
        </div>
      )}

      {run && run.status === "done" && result && !hasSchedule && (
        <div className={panelClass} style={{ animationDelay: "0.2s" }}>
          <div className={hintClass}>Schedule data is empty.</div>
        </div>
      )}

      {run && run.status === "done" && !result && (
        <div className={panelClass} style={{ animationDelay: "0.15s" }}>
          <div className={panelTitleClass}>Result file</div>
          <div className={hintClass}>Not ready yet. Polling continues.</div>
        </div>
      )}
    </section>
  );
}

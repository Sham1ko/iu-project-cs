import { useMemo } from "react";
import ScheduleTable from "./ScheduleTable";
import StatusBadge from "./StatusBadge";
import type { GenerationRun, ScheduleByDay, TimetableResultPayload } from "../types/api";
import { formatDateTime } from "../utils/format";
import { collectClassNames, collectLessonsForClass, getScheduleDays } from "../utils/schedule";
import { Progress } from "@/components/ui/progress";
import { getRunPdfUrl } from "../api/timetables";

interface RunStatusResultProps {
  run: GenerationRun;
  result: TimetableResultPayload | null;
  lastSubmittedGenerations: number | null;
  pdfDeleted: boolean;
  isDeleting: boolean;
  onDeletePdf: () => void;
  panelClass: string;
  panelTitleClass: string;
  hintClass: string;
  labelClass: string;
  valueClass: string;
  secondaryButtonClass: string;
  dangerButtonClass: string;
  disabledButtonClass: string;
}

export default function RunStatusResult({
  run,
  result,
  lastSubmittedGenerations,
  pdfDeleted,
  isDeleting,
  onDeletePdf,
  panelClass,
  panelTitleClass,
  hintClass,
  labelClass,
  valueClass,
  secondaryButtonClass,
  dangerButtonClass,
  disabledButtonClass,
}: RunStatusResultProps) {
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
    if (!Number.isFinite(seconds) || seconds < 0) return "-";
    const rounded = Math.round(seconds);
    if (rounded < 60) return `${rounded}s`;
    const minutes = Math.floor(rounded / 60);
    const remainingSeconds = rounded % 60;
    if (minutes < 60) return `${minutes}m ${remainingSeconds}s`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m`;
  };

  const generationsFromRun = useMemo(() => {
    const params = run.params as Record<string, unknown> | undefined;
    const rawValue = params?.generations;
    const numericValue =
      typeof rawValue === "number"
        ? rawValue
        : typeof rawValue === "string"
          ? Number(rawValue)
          : undefined;
    if (!Number.isFinite(numericValue) || !numericValue) return null;
    return numericValue;
  }, [run.params]);

  const generationsDisplay = generationsFromRun ?? lastSubmittedGenerations;
  const generationsValueLabel = generationsDisplay ? `${generationsDisplay}` : "Default (200)";

  const startedAt = run.started_at ? new Date(run.started_at) : null;
  const finishedAt = run.finished_at ? new Date(run.finished_at) : null;
  const durationSeconds =
    startedAt && finishedAt ? (finishedAt.getTime() - startedAt.getTime()) / 1000 : null;

  const finishedValue = () => {
    if (run.status === "running") return formatDateTime(run.finished_at);
    if (run.status === "done") {
      const finishedLabel = formatDateTime(run.finished_at);
      const durationLabel = durationSeconds ? ` (${formatDuration(durationSeconds)})` : "";
      return `${finishedLabel}${durationLabel}`;
    }
    return formatDateTime(run.finished_at);
  };

  return (
    <>
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

      {run.status === "done" && result && (
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
                onClick={onDeletePdf}
                disabled={isDeleting || pdfDeleted}
              >
                {pdfDeleted ? "Deleted" : isDeleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
          {pdfDeleted && <div className={hintClass}>PDF has been deleted.</div>}
        </div>
      )}

      {run.status === "done" && result && (
        <div className={panelClass} style={{ animationDelay: "0.18s" }}>
          <div className={panelTitleClass}>Schedule preview</div>
          <div className={hintClass}>Per-class timetable for Monday to Friday.</div>
        </div>
      )}

      {run.status === "done" && result && hasSchedule && (
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

      {run.status === "done" && result && !hasSchedule && (
        <div className={panelClass} style={{ animationDelay: "0.2s" }}>
          <div className={hintClass}>Schedule data is empty.</div>
        </div>
      )}

      {run.status === "done" && !result && (
        <div className={panelClass} style={{ animationDelay: "0.15s" }}>
          <div className={panelTitleClass}>Result file</div>
          <div className={hintClass}>Not ready yet. Polling continues.</div>
        </div>
      )}
    </>
  );
}

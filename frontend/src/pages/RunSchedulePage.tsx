import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { getRunResult, getRunStatus } from "../api/timetables";
import ScheduleNav from "../components/ScheduleNav";
import ScheduleTable from "../components/ScheduleTable";
import StatusBadge from "../components/StatusBadge";
import type { GenerationRun, ScheduleByDay, TimetableResultPayload } from "../types/api";
import { formatDateTime } from "../utils/format";
import {
  collectClassNames,
  collectLessonsForClass,
  getScheduleDays,
} from "../utils/schedule";

const toAnchorId = (label: string) =>
  `day-${label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "")}`;

export default function RunSchedulePage() {
  const { runId } = useParams();
  const parsedRunId = Number(runId);
  const [run, setRun] = useState<GenerationRun | null>(null);
  const [result, setResult] = useState<TimetableResultPayload | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  useEffect(() => {
    if (!Number.isFinite(parsedRunId)) {
      setError("Run id is missing or invalid. Open this page from Runs.");
      return;
    }

    let active = true;

    const load = async () => {
      setIsLoading(true);
      setError(null);
      setInfo(null);
      try {
        const runData = await getRunStatus(parsedRunId);
        if (!active) {
          return;
        }
        setRun(runData);

        if (runData.status !== "done") {
          setInfo(
            `Result not ready yet. Current status: ${runData.status}. Try again after it finishes.`,
          );
          setResult(null);
          return;
        }

        const payload = await getRunResult(parsedRunId);
        if (!active) {
          return;
        }
        setResult(payload);
      } catch (err) {
        if (!active) {
          return;
        }
        const apiError = err instanceof ApiError ? err : null;
        if (apiError?.status === 409) {
          setInfo(apiError.message);
        } else {
          setError(apiError?.message ?? "Failed to load schedule.");
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    };

    load();

    return () => {
      active = false;
    };
  }, [parsedRunId]);

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
  const navItems = useMemo(
    () => classNames.map((className) => ({ id: toAnchorId(className), label: className })),
    [classNames],
  );

  const hasSchedule =
    days.length > 0 &&
    classNames.length > 0 &&
    classNames.some((className) => (lessonsByClass[className]?.length ?? 0) > 0);

  return (
    <section className="page">
      <div className="page-head page-head-split">
        <div>
          <h1>Schedule View</h1>
          <p>Explore the day-by-day timetable for this run.</p>
        </div>
        <div className="page-head-actions">
          <Link className="button button-secondary" to="/runs">
            Back to Runs
          </Link>
        </div>
      </div>

      {(error || info) && (
        <div
          className={`panel banner ${error ? "banner-error" : "banner-info"}`}
          role="status"
          aria-live="polite"
        >
          {error || info}
        </div>
      )}

      {isLoading && (
        <div className="panel" style={{ animationDelay: "0.05s" }}>
          <div className="hint">Loading schedule…</div>
        </div>
      )}

      {run && (
        <div className="panel" style={{ animationDelay: "0.08s" }}>
          <div className="panel-title">Run Summary</div>
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
              <div className="label">Created</div>
              <div className="value">{formatDateTime(run.created_at)}</div>
            </div>
            <div>
              <div className="label">Finished</div>
              <div className="value">{formatDateTime(run.finished_at)}</div>
            </div>
            {result && (
              <>
                <div>
                  <div className="label">Fitness score</div>
                  <div className="value">{result.fitness_score}</div>
                </div>
                <div>
                  <div className="label">Generation</div>
                  <div className="value">{result.generation}</div>
                </div>
                <div>
                  <div className="label">Total lessons</div>
                  <div className="value">{result.statistics.total_lessons}</div>
                </div>
                <div>
                  <div className="label">Teacher conflicts</div>
                  <div className="value">{result.statistics.teacher_conflicts}</div>
                </div>
                <div>
                  <div className="label">Teacher gaps</div>
                  <div className="value">{result.statistics.teacher_gaps}</div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {result && hasSchedule && (
        <div className="schedule-layout" style={{ animationDelay: "0.12s" }}>
          <ScheduleNav items={navItems} />

          <div className="schedule-content">
            {classNames.map((className) => (
              <ScheduleTable
                key={className}
                anchorId={toAnchorId(className)}
                classLabel={className}
                days={days}
                lessons={lessonsByClass[className] ?? []}
                schedule={schedule}
              />
            ))}
          </div>
        </div>
      )}

      {result && !hasSchedule && (
        <div className="panel" style={{ animationDelay: "0.12s" }}>
          <div className="hint">
            Schedule data is empty. Generate a new run or check the backend output.
          </div>
        </div>
      )}
    </section>
  );
}

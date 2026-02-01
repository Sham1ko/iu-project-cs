import type { ScheduleByDay, ScheduleEntry } from "../types/api";

const renderEntry = (entry: ScheduleEntry | null | undefined) => {
  if (!entry) {
    return <span className="text-muted">-</span>;
  }
  return (
    <div className="schedule-cell">
      <div className="schedule-subject">{entry.subject}</div>
      <div className="schedule-teacher">{entry.teacher}</div>
    </div>
  );
};

type ScheduleTableProps = {
  anchorId?: string;
  classLabel: string;
  days: string[];
  lessons: string[];
  schedule: ScheduleByDay;
};

export default function ScheduleTable({
  anchorId,
  classLabel,
  days,
  lessons,
  schedule,
}: ScheduleTableProps) {
  return (
    <section id={anchorId} className="panel schedule-day">
      <div className="schedule-day-title">
        <h2>{classLabel}</h2>
        <span className="schedule-day-meta">{lessons.length} lessons</span>
      </div>
      <div className="schedule-table-wrapper">
        <table className="schedule-table">
          <caption className="visually-hidden">Schedule for {classLabel}</caption>
          <thead>
            <tr>
              <th scope="col">Lesson</th>
              {days.map((day) => (
                <th scope="col" key={day}>
                  {day}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {lessons.map((lesson) => (
              <tr key={lesson}>
                <th scope="row">{lesson}</th>
                {days.map((day) => (
                  <td key={day}>{renderEntry(schedule[day]?.[lesson]?.[classLabel])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

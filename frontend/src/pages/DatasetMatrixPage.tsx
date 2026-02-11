import { useState } from "react";

type SubjectRow = {
  id: string;
  teacher: string;
  cells: Record<string, string>;
};

type SubjectTable = {
  id: string;
  name: string;
  rows: SubjectRow[];
  teacherDraft: string;
};

const DEFAULT_GROUPS = ["9A", "9B", "9C"];

const createRow = (
  teacher: string,
  groups: string[],
  values: Record<string, string> = {},
): SubjectRow => ({
  id: `${teacher}-${Math.random().toString(36).slice(2, 9)}`,
  teacher,
  cells: groups.reduce<Record<string, string>>((acc, group) => {
    acc[group] = values[group] ?? "";
    return acc;
  }, {}),
});

const createInitialSubjects = (groups: string[]): SubjectTable[] => [
  {
    id: "subject-1",
    name: "Subject #1",
    teacherDraft: "",
    rows: [
      createRow("Teacher X", groups, { "9A": "0", "9B": "0" }),
      createRow("Teacher Y", groups, { "9A": "0", "9B": "0", "9C": "x" }),
    ],
  },
  {
    id: "subject-2",
    name: "Subject #2",
    teacherDraft: "",
    rows: [
      createRow("Teacher X", groups, { "9A": "", "9B": "x", "9C": "0" }),
      createRow("Teacher Y", groups, { "9A": "0", "9B": "0", "9C": "0" }),
    ],
  },
];

export default function DatasetMatrixPage() {
  const [groups] = useState(DEFAULT_GROUPS);
  const [subjects, setSubjects] = useState<SubjectTable[]>(() =>
    createInitialSubjects(DEFAULT_GROUPS),
  );

  const handleTeacherDraftChange = (subjectIndex: number, value: string) => {
    setSubjects((prev) =>
      prev.map((subject, index) =>
        index === subjectIndex ? { ...subject, teacherDraft: value } : subject,
      ),
    );
  };

  const handleAddTeacher = (subjectIndex: number) => {
    setSubjects((prev) =>
      prev.map((subject, index) => {
        if (index !== subjectIndex) {
          return subject;
        }
        const teacherName = subject.teacherDraft.trim();
        if (!teacherName) {
          return subject;
        }
        const newRow = createRow(teacherName, groups);
        return {
          ...subject,
          rows: [...subject.rows, newRow],
          teacherDraft: "",
        };
      }),
    );
  };

  const handleCellChange = (
    subjectIndex: number,
    rowId: string,
    group: string,
    value: string,
  ) => {
    setSubjects((prev) =>
      prev.map((subject, index) => {
        if (index !== subjectIndex) {
          return subject;
        }
        const rows = subject.rows.map((row) =>
          row.id === rowId ? { ...row, cells: { ...row.cells, [group]: value } } : row,
        );
        return { ...subject, rows };
      }),
    );
  };

  return (
    <section className="grid gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold leading-tight">Lesson matrix</h1>
          <p className="text-sm text-[var(--muted)]">
            Table per subject: teachers on the left, groups on top.
          </p>
        </div>
      </div>

      {subjects.map((subject, subjectIndex) => (
        <div
          key={subject.id}
          className="rounded-[18px] border border-[var(--border)] bg-[var(--surface)] px-[22px] py-5 shadow-[var(--shadow)]"
        >
          <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="text-[0.95rem] font-semibold">{subject.name}</div>
              <div className="text-sm text-[var(--muted)]">
                Fill availability or hours for each teacher.
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <input
                className="h-10 w-56 rounded-lg border border-[var(--border)] bg-[var(--surface-strong)] px-3 text-sm"
                value={subject.teacherDraft}
                onChange={(event) => handleTeacherDraftChange(subjectIndex, event.target.value)}
                placeholder="Add teacher"
              />
              <button
                className="inline-flex h-10 items-center justify-center rounded-lg border border-[var(--border)] bg-white px-3.5 text-sm font-medium text-[var(--text)] transition hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[rgba(15,118,110,0.4)] disabled:cursor-not-allowed disabled:opacity-60"
                type="button"
                onClick={() => handleAddTeacher(subjectIndex)}
                disabled={!subject.teacherDraft.trim()}
              >
                Add teacher
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] border-separate border-spacing-y-2">
              <thead>
                <tr className="text-left text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
                  <th className="w-48 px-3 pb-2">Teacher</th>
                  {groups.map((group) => (
                    <th key={`${subject.id}-${group}`} className="px-2 pb-2 text-center">
                      {group}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {subject.rows.length === 0 ? (
                  <tr>
                    <td
                      className="rounded-lg border border-dashed border-[var(--border)] px-3 py-4 text-sm text-[var(--muted)]"
                      colSpan={groups.length + 1}
                    >
                      Add a teacher to start filling the table.
                    </td>
                  </tr>
                ) : (
                  subject.rows.map((row) => (
                    <tr key={row.id}>
                      <td className="rounded-l-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm font-medium">
                        {row.teacher}
                      </td>
                      {groups.map((group, index) => (
                        <td
                          key={`${row.id}-${group}`}
                          className={`border border-[var(--border)] bg-[var(--surface)] px-2 py-2 text-center ${
                            index === groups.length - 1 ? "rounded-r-lg" : ""
                          }`}
                        >
                          <input
                            className="h-9 w-full rounded-md border border-[var(--border)] bg-[var(--surface-strong)] text-center text-sm"
                            value={row.cells[group] ?? ""}
                            onChange={(event) =>
                              handleCellChange(subjectIndex, row.id, group, event.target.value)
                            }
                            placeholder="0"
                          />
                        </td>
                      ))}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </section>
  );
}

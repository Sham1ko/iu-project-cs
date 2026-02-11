import { useMemo, useState } from "react";
import { X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";

const DEFAULT_GROUPS = [""];

type LessonEntry = {
  name: string;
  hours: string;
};

type GroupLessons = {
  label: string;
  lessons: LessonEntry[];
};

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

export default function CreateDatasetPage() {
  const [datasetName, setDatasetName] = useState("");
  const [groups, setGroups] = useState(DEFAULT_GROUPS);
  const [step, setStep] = useState<"groups" | "lessons" | "matrix">("groups");
  const [groupError, setGroupError] = useState<string | null>(null);
  const [lessonsByGroup, setLessonsByGroup] = useState<GroupLessons[]>([]);
  const [matrixSubjects, setMatrixSubjects] = useState<SubjectTable[]>([]);
  const [copyDialogOpen, setCopyDialogOpen] = useState(false);
  const [copySourceIndex, setCopySourceIndex] = useState<number | null>(null);
  const [copyTargets, setCopyTargets] = useState<Record<number, boolean>>({});

  const panelClass =
    "rounded-[18px] border border-[var(--border)] bg-[var(--surface)] px-[22px] py-5 shadow-[var(--shadow)] animate-[rise_0.5s_ease_both]";
  const panelTitleClass = "mb-4 text-[0.95rem] font-semibold";
  const hintClass = "text-sm text-[var(--muted)]";
  const fieldClass = "grid gap-2 text-sm";
  const inputClass =
    "h-10 w-full rounded-lg border border-[var(--border)] bg-[var(--surface-strong)] px-3 text-sm";
  const primaryButtonClass =
    "inline-flex items-center justify-center rounded-lg bg-[var(--accent)] px-5 py-3 font-semibold text-white shadow-[0_12px_30px_rgba(15,118,110,0.24)] transition hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[rgba(15,118,110,0.5)] disabled:cursor-not-allowed disabled:opacity-65 disabled:shadow-none";
  const secondaryButtonClass =
    "inline-flex items-center justify-center rounded-lg border border-[var(--border)] bg-white px-3.5 py-2.5 text-sm font-medium text-[var(--text)] transition hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[rgba(15,118,110,0.4)] disabled:cursor-not-allowed disabled:opacity-60";
  const iconButtonClass = `${secondaryButtonClass} h-10 w-10 min-w-[40px] !p-0`;

  const canProceed = useMemo(() => groups.some((group) => group.trim().length > 0), [groups]);
  const normalizedGroups = useMemo(
    () => groups.map((group, index) => group.trim() || `Group ${index + 1}`),
    [groups],
  );
  const copySource = copySourceIndex !== null ? lessonsByGroup[copySourceIndex] : null;
  const copyTargetOptions = useMemo(
    () =>
      copySourceIndex === null
        ? []
        : lessonsByGroup
            .map((group, index) => ({ group, index }))
            .filter(({ index }) => index !== copySourceIndex),
    [copySourceIndex, lessonsByGroup],
  );
  const hasSelectedCopyTargets = useMemo(
    () => Object.values(copyTargets).some(Boolean),
    [copyTargets],
  );

  const groupLabel = (group: string, index: number) =>
    group.trim().length > 0 ? group.trim() : `Group ${index + 1}`;

  const buildLessonGroups = (sourceGroups: string[], existing: GroupLessons[]) =>
    sourceGroups.map((group, index) => {
      const label = groupLabel(group, index);
      const current = existing[index];
      if (current) {
        const lessons = current.lessons.length > 0 ? current.lessons : [{ name: "", hours: "" }];
        return { ...current, label, lessons };
      }
      return { label, lessons: [{ name: "", hours: "" }] };
    });

  const createMatrixRow = (teacher: string, groupNames: string[]): SubjectRow => ({
    id: `${teacher}-${Math.random().toString(36).slice(2, 9)}`,
    teacher,
    cells: groupNames.reduce<Record<string, string>>((acc, group) => {
      acc[group] = "";
      return acc;
    }, {}),
  });

  const normalizeMatrixRow = (row: SubjectRow, groupNames: string[]): SubjectRow => ({
    ...row,
    cells: groupNames.reduce<Record<string, string>>((acc, group) => {
      acc[group] = row.cells[group] ?? "";
      return acc;
    }, {}),
  });

  const buildMatrixSubjects = (
    groupNames: string[],
    lessonGroups: GroupLessons[],
    existing: SubjectTable[],
  ): SubjectTable[] => {
    const subjectNames: string[] = [];
    const seen = new Set<string>();
    lessonGroups.forEach((group) => {
      group.lessons.forEach((lesson) => {
        const name = lesson.name.trim();
        if (!name || seen.has(name)) {
          return;
        }
        seen.add(name);
        subjectNames.push(name);
      });
    });
    if (subjectNames.length === 0) {
      subjectNames.push("Subject #1");
    }
    const existingByName = new Map(existing.map((subject) => [subject.name, subject]));
    return subjectNames.map((name) => {
      const current = existingByName.get(name);
      return {
        id: current?.id ?? `${name}-${Math.random().toString(36).slice(2, 9)}`,
        name,
        teacherDraft: current?.teacherDraft ?? "",
        rows: current?.rows
          ? current.rows.map((row) => normalizeMatrixRow(row, groupNames))
          : [],
      };
    });
  };

  const handleGroupChange = (index: number, value: string) => {
    setGroups((prev) => {
      const next = [...prev];
      next[index] = value;
      return next;
    });
  };

  const handleAddGroup = () => {
    setGroups((prev) => [...prev, ""]);
  };

  const handleRemoveGroup = (index: number) => {
    setGroups((prev) => {
      const next = prev.filter((_, idx) => idx !== index);
      return next.length > 0 ? next : [""];
    });
  };

  const handleReset = () => {
    setDatasetName("");
    setGroups(DEFAULT_GROUPS);
    setLessonsByGroup([]);
    setMatrixSubjects([]);
    setGroupError(null);
    setStep("groups");
    setCopyDialogOpen(false);
    setCopySourceIndex(null);
    setCopyTargets({});
  };

  const handleNextStep = () => {
    if (!canProceed) {
      setGroupError("Add at least one group to continue.");
      return;
    }
    setGroupError(null);
    setLessonsByGroup((prev) => buildLessonGroups(groups, prev));
    setStep("lessons");
  };

  const handleBackToGroups = () => {
    setCopyDialogOpen(false);
    setCopySourceIndex(null);
    setCopyTargets({});
    setStep("groups");
  };

  const handleNextToMatrix = () => {
    setMatrixSubjects((prev) => buildMatrixSubjects(normalizedGroups, lessonsByGroup, prev));
    setStep("matrix");
  };

  const handleBackToLessons = () => {
    setStep("lessons");
  };

  const handleLessonChange = (
    groupIndex: number,
    lessonIndex: number,
    key: keyof LessonEntry,
    value: string,
  ) => {
    setLessonsByGroup((prev) =>
      prev.map((group, gIndex) => {
        if (gIndex !== groupIndex) {
          return group;
        }
        const lessons = group.lessons.map((lesson, lIndex) =>
          lIndex === lessonIndex ? { ...lesson, [key]: value } : lesson,
        );
        return { ...group, lessons };
      }),
    );
  };

  const handleAddLesson = (groupIndex: number) => {
    setLessonsByGroup((prev) =>
      prev.map((group, index) =>
        index === groupIndex
          ? { ...group, lessons: [...group.lessons, { name: "", hours: "" }] }
          : group,
      ),
    );
  };

  const handleRemoveLesson = (groupIndex: number, lessonIndex: number) => {
    setLessonsByGroup((prev) =>
      prev.map((group, index) => {
        if (index !== groupIndex) {
          return group;
        }
        const nextLessons = group.lessons.filter((_, lIndex) => lIndex !== lessonIndex);
        return {
          ...group,
          lessons: nextLessons.length > 0 ? nextLessons : [{ name: "", hours: "" }],
        };
      }),
    );
  };

  const handleOpenCopyDialog = (groupIndex: number) => {
    setCopySourceIndex(groupIndex);
    setCopyTargets({});
    setCopyDialogOpen(true);
  };

  const handleCloseCopyDialog = () => {
    setCopyDialogOpen(false);
    setCopySourceIndex(null);
    setCopyTargets({});
  };

  const handleToggleCopyTarget = (
    targetIndex: number,
    checked: boolean | "indeterminate",
  ) => {
    const isChecked = checked === true;
    setCopyTargets((prev) => ({ ...prev, [targetIndex]: isChecked }));
  };

  const handleConfirmCopy = () => {
    if (copySourceIndex === null || !hasSelectedCopyTargets) {
      return;
    }
    setLessonsByGroup((prev) => {
      const source = prev[copySourceIndex];
      if (!source) {
        return prev;
      }
      return prev.map((group, index) => {
        if (!copyTargets[index] || index === copySourceIndex) {
          return group;
        }
        const lessons =
          source.lessons.length > 0
            ? source.lessons.map((lesson) => ({ ...lesson }))
            : [{ name: "", hours: "" }];
        return { ...group, lessons };
      });
    });
    handleCloseCopyDialog();
  };

  const handleMatrixTeacherDraftChange = (subjectIndex: number, value: string) => {
    setMatrixSubjects((prev) =>
      prev.map((subject, index) =>
        index === subjectIndex ? { ...subject, teacherDraft: value } : subject,
      ),
    );
  };

  const handleMatrixAddTeacher = (subjectIndex: number) => {
    setMatrixSubjects((prev) =>
      prev.map((subject, index) => {
        if (index !== subjectIndex) {
          return subject;
        }
        const teacherName = subject.teacherDraft.trim();
        if (!teacherName) {
          return subject;
        }
        const newRow = createMatrixRow(teacherName, normalizedGroups);
        return {
          ...subject,
          rows: [...subject.rows, newRow],
          teacherDraft: "",
        };
      }),
    );
  };

  const handleMatrixCellChange = (
    subjectIndex: number,
    rowId: string,
    group: string,
    value: string,
  ) => {
    setMatrixSubjects((prev) =>
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
          <h1 className="text-2xl font-semibold leading-tight">New dataset</h1>
          <p className="text-sm text-[var(--muted)]">
            Draft UI only (no requests yet). Start with groups.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button className={primaryButtonClass} type="button" disabled>
            Save dataset
          </button>
        </div>
      </div>

      {step === "groups" && (
        <div className={`${panelClass} [animation-delay:0.05s]`}>
          <div className={panelTitleClass}>Step 1 - Groups</div>
          <div className="grid gap-4">
            <label className={fieldClass}>
              <span>Name</span>
              <input
                className={inputClass}
                value={datasetName}
                onChange={(event) => setDatasetName(event.target.value)}
                placeholder="Dataset name"
              />
            </label>

            <div className={fieldClass}>
              <span>Groups</span>
              <div className={hintClass}>Fill group names, then continue.</div>
              <div className="grid gap-3">
                {groups.map((group, index) => (
                  <div key={`group-${index}`} className="flex items-center gap-3">
                    <input
                      className={`${inputClass} flex-1`}
                      value={group}
                      onChange={(event) => handleGroupChange(index, event.target.value)}
                      placeholder="e.g., 9A"
                      aria-label={`Group ${index + 1}`}
                    />
                    <button
                      className={iconButtonClass}
                      type="button"
                      onClick={() => handleRemoveGroup(index)}
                      aria-label={`Remove group ${index + 1}`}
                    >
                      <X size={16} />
                    </button>
                  </div>
                ))}
              </div>
              {groupError && <div className="text-sm text-[var(--error)]">{groupError}</div>}
            </div>

            <div className="flex flex-wrap gap-3">
              <button className={secondaryButtonClass} type="button" onClick={handleAddGroup}>
                Add group
              </button>
              <button className={secondaryButtonClass} type="button" onClick={handleReset}>
                Reset
              </button>
              <button
                className={primaryButtonClass}
                type="button"
                onClick={handleNextStep}
                disabled={!canProceed}
              >
                Next step
              </button>
            </div>
          </div>
        </div>
      )}

      {step === "lessons" && (
        <div className={`${panelClass} [animation-delay:0.1s]`}>
          <div className={panelTitleClass}>Step 2 - Lessons and hours</div>
          <div className="grid gap-4">
            <div className={hintClass}>For each group, add lessons and specify weekly hours.</div>

            <Dialog
              open={copyDialogOpen}
              onOpenChange={(open) => {
                if (!open) {
                  handleCloseCopyDialog();
                }
              }}
            >
              {lessonsByGroup.map((group, groupIndex) => (
                <div
                  key={`lesson-group-${groupIndex}`}
                  className="rounded-[14px] border border-[var(--border)] bg-[var(--surface-strong)] p-4"
                >
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div className="font-semibold">{group.label}</div>
                    <DialogTrigger asChild>
                      <button
                        className={secondaryButtonClass}
                        type="button"
                        onClick={() => handleOpenCopyDialog(groupIndex)}
                      >
                        Copy
                      </button>
                    </DialogTrigger>
                  </div>
                  <div className="grid gap-3">
                    {group.lessons.map((lesson, lessonIndex) => (
                      <div
                        key={`lesson-${groupIndex}-${lessonIndex}`}
                        className="grid items-end gap-3 sm:grid-cols-[minmax(0,1fr)_160px_auto]"
                      >
                        <label className={fieldClass}>
                          <span>Lesson</span>
                          <input
                            className={inputClass}
                            value={lesson.name}
                            onChange={(event) =>
                              handleLessonChange(
                                groupIndex,
                                lessonIndex,
                                "name",
                                event.target.value,
                              )
                            }
                            placeholder="e.g., Math"
                          />
                        </label>
                        <label className={fieldClass}>
                          <span>Hours</span>
                          <input
                            className={inputClass}
                            value={lesson.hours}
                            onChange={(event) =>
                              handleLessonChange(
                                groupIndex,
                                lessonIndex,
                                "hours",
                                event.target.value,
                              )
                            }
                            inputMode="numeric"
                            placeholder="0"
                          />
                        </label>
                        <button
                          className={`${iconButtonClass} self-end`}
                          type="button"
                          onClick={() => handleRemoveLesson(groupIndex, lessonIndex)}
                          aria-label={`Remove lesson ${lessonIndex + 1} from ${group.label}`}
                        >
                          <X size={16} />
                        </button>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-3">
                    <button
                      className={secondaryButtonClass}
                      type="button"
                      onClick={() => handleAddLesson(groupIndex)}
                    >
                      Add lesson
                    </button>
                  </div>
                </div>
              ))}

              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>Copy lessons</DialogTitle>
                  <DialogDescription>
                    {copySource
                      ? `Select groups to receive lessons from ${copySource.label}.`
                      : "Select groups to receive lessons."}
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-3">
                  {copyTargetOptions.length === 0 ? (
                    <div className={hintClass}>Add another group to enable copying.</div>
                  ) : (
                    copyTargetOptions.map(({ group, index }) => (
                      <label
                        key={`copy-target-${index}`}
                        className="flex items-center gap-3 rounded-lg border border-[var(--border)] bg-[var(--surface-strong)] px-3 py-2"
                      >
                        <Checkbox
                          checked={Boolean(copyTargets[index])}
                          onCheckedChange={(checked) =>
                            handleToggleCopyTarget(index, checked)
                          }
                        />
                        <span className="text-sm font-medium">{group.label}</span>
                      </label>
                    ))
                  )}
                </div>
                <div className="flex flex-wrap justify-end gap-3">
                  <button
                    className={secondaryButtonClass}
                    type="button"
                    onClick={handleCloseCopyDialog}
                  >
                    Cancel
                  </button>
                  <button
                    className={primaryButtonClass}
                    type="button"
                    onClick={handleConfirmCopy}
                    disabled={!hasSelectedCopyTargets}
                  >
                    Copy lessons
                  </button>
                </div>
              </DialogContent>
            </Dialog>

            <div className="flex flex-wrap gap-3">
              <button className={secondaryButtonClass} type="button" onClick={handleBackToGroups}>
                Back to groups
              </button>
              <button className={primaryButtonClass} type="button" onClick={handleNextToMatrix}>
                Next step
              </button>
            </div>
          </div>
        </div>
      )}

      {step === "matrix" && (
        <div className={`${panelClass} [animation-delay:0.15s]`}>
          <div className={panelTitleClass}>Step 3 - Lesson matrix</div>
          <div className="grid gap-4">
            <div className={hintClass}>
              Teachers on the left, groups across the top. Fill availability or hours per subject.
            </div>

            {matrixSubjects.length === 0 ? (
              <div className={hintClass}>Add lessons first to build the matrix.</div>
            ) : (
              matrixSubjects.map((subject, subjectIndex) => (
                <div
                  key={subject.id}
                  className="rounded-[14px] border border-[var(--border)] bg-[var(--surface-strong)] p-4"
                >
                  <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <div className="text-[0.95rem] font-semibold">{subject.name}</div>
                      <div className={hintClass}>Add teachers for this subject.</div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <input
                        className="h-10 w-56 rounded-lg border border-[var(--border)] bg-[var(--surface-strong)] px-3 text-sm"
                        value={subject.teacherDraft}
                        onChange={(event) =>
                          handleMatrixTeacherDraftChange(subjectIndex, event.target.value)
                        }
                        placeholder="Add teacher"
                      />
                      <button
                        className={secondaryButtonClass}
                        type="button"
                        onClick={() => handleMatrixAddTeacher(subjectIndex)}
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
                          {normalizedGroups.map((group) => (
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
                              colSpan={normalizedGroups.length + 1}
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
                              {normalizedGroups.map((group, index) => (
                                <td
                                  key={`${row.id}-${group}`}
                                  className={`border border-[var(--border)] bg-[var(--surface)] px-2 py-2 text-center ${
                                    index === normalizedGroups.length - 1 ? "rounded-r-lg" : ""
                                  }`}
                                >
                                  <input
                                    className="h-9 w-full rounded-md border border-[var(--border)] bg-[var(--surface-strong)] text-center text-sm"
                                    value={row.cells[group] ?? ""}
                                    onChange={(event) =>
                                      handleMatrixCellChange(
                                        subjectIndex,
                                        row.id,
                                        group,
                                        event.target.value,
                                      )
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
              ))
            )}

            <div className="flex flex-wrap gap-3">
              <button className={secondaryButtonClass} type="button" onClick={handleBackToLessons}>
                Back to lessons
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

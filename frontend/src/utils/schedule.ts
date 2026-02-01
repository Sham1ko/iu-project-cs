import type { ScheduleByDay } from "../types/api";

export const WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

export const sortDays = (keys: string[]) => {
  const order = new Map(WEEKDAYS.map((day, index) => [day, index]));
  return [...keys].sort((a, b) => {
    const orderA = order.get(a);
    const orderB = order.get(b);
    if (orderA !== undefined || orderB !== undefined) {
      return (orderA ?? Number.POSITIVE_INFINITY) - (orderB ?? Number.POSITIVE_INFINITY);
    }
    return a.localeCompare(b);
  });
};

export const getScheduleDays = (schedule: ScheduleByDay) => {
  const availableDays = sortDays(Object.keys(schedule));
  const weekdayDays = WEEKDAYS.filter((day) => availableDays.includes(day));
  return weekdayDays.length > 0 ? weekdayDays : WEEKDAYS;
};

const parseClassName = (value: string) => {
  const trimmed = value.trim();
  const match = trimmed.match(/^(\d+)\s*([A-Za-z]+)?$/);
  if (match) {
    return {
      number: Number.parseInt(match[1], 10),
      suffix: (match[2] ?? "").toUpperCase(),
      raw: trimmed,
    };
  }
  const numMatch = trimmed.match(/^(\d+)/);
  if (numMatch) {
    return {
      number: Number.parseInt(numMatch[1], 10),
      suffix: trimmed.slice(numMatch[1].length).trim().toUpperCase(),
      raw: trimmed,
    };
  }
  return {
    number: null as number | null,
    suffix: trimmed.toUpperCase(),
    raw: trimmed,
  };
};

const compareClassNames = (left: string, right: string) => {
  const parsedLeft = parseClassName(left);
  const parsedRight = parseClassName(right);
  if (parsedLeft.number !== null && parsedRight.number !== null) {
    if (parsedLeft.number !== parsedRight.number) {
      return parsedLeft.number - parsedRight.number;
    }
    const suffixCompare = parsedLeft.suffix.localeCompare(parsedRight.suffix);
    if (suffixCompare !== 0) {
      return suffixCompare;
    }
    return parsedLeft.raw.localeCompare(parsedRight.raw);
  }
  if (parsedLeft.number !== null) {
    return -1;
  }
  if (parsedRight.number !== null) {
    return 1;
  }
  return parsedLeft.raw.localeCompare(parsedRight.raw, undefined, {
    numeric: true,
    sensitivity: "base",
  });
};

export const collectClassNames = (schedule: ScheduleByDay) => {
  const classNames = new Set<string>();
  for (const daySchedule of Object.values(schedule)) {
    for (const lessonSchedule of Object.values(daySchedule ?? {})) {
      for (const className of Object.keys(lessonSchedule ?? {})) {
        classNames.add(className);
      }
    }
  }
  return Array.from(classNames).sort(compareClassNames);
};

export const collectLessonsForClass = (
  schedule: ScheduleByDay,
  className: string,
  days: string[],
) => {
  const lessons = new Set<string>();
  for (const day of days) {
    const daySchedule = schedule[day];
    if (!daySchedule) {
      continue;
    }
    for (const lesson of Object.keys(daySchedule)) {
      lessons.add(lesson);
    }
  }
  return [...lessons].sort((a, b) => Number(a) - Number(b));
};

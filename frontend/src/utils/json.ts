export const safeJsonParse = (value: string) => {
  try {
    return { ok: true, value: JSON.parse(value) } as const;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Invalid JSON";
    return { ok: false, error: message } as const;
  }
};

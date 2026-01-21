import type { GenerationStatus } from "../types/api";

const labelMap: Record<GenerationStatus, string> = {
  queued: "Queued",
  running: "Running",
  done: "Done",
  failed: "Failed",
};

export default function StatusBadge({ status }: { status: GenerationStatus }) {
  return <span className={`status status-${status}`}>{labelMap[status]}</span>;
}

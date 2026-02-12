import { useEffect, useState } from "react";
import { listDatasets } from "../api/datasets";
import type { Dataset } from "../types/api";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface RunConfigurationProps {
  datasetId: string;
  generations: string;
  isSubmitting: boolean;
  onDatasetIdChange: (value: string) => void;
  onGenerationsChange: (value: string) => void;
  onGenerate: () => void;
  panelClass: string;
  panelTitleClass: string;
  hintClass: string;
  primaryButtonClass: string;
}

export default function RunConfiguration({
  datasetId,
  generations,
  isSubmitting,
  onDatasetIdChange,
  onGenerationsChange,
  onGenerate,
  panelClass,
  panelTitleClass,
  hintClass,
  primaryButtonClass,
}: RunConfigurationProps) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);

  useEffect(() => {
    const loadDatasets = async () => {
      try {
        const data = await listDatasets();
        setDatasets(data);
      } catch (err) {
        console.error("Failed to load datasets:", err);
      }
    };
    loadDatasets();
  }, []);

  return (
    <div className={panelClass} style={{ animationDelay: "0.05s" }}>
      <div className={panelTitleClass}>Run configuration</div>
      <div className="grid gap-4 items-end md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
        <label className="grid gap-2 text-sm">
          <span>Dataset (optional)</span>
          <Select
            value={datasetId || undefined}
            onValueChange={(value) => onDatasetIdChange(value || "")}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Latest dataset" />
            </SelectTrigger>
            <SelectContent>
              {datasets.map((dataset) => (
                <SelectItem key={dataset.id} value={String(dataset.id)}>
                  {dataset.id} - {dataset.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </label>
        <label className="grid gap-2 text-sm">
          <span>Generations (optional)</span>
          <input
            className="w-full rounded-xl border border-border bg-(--surface-strong) px-3 py-2 text-sm"
            type="number"
            min={1}
            step={1}
            value={generations}
            onChange={(event) => onGenerationsChange(event.target.value)}
            placeholder="Default: 200"
          />
        </label>
        <button className={primaryButtonClass} onClick={onGenerate} disabled={isSubmitting}>
          {isSubmitting ? "Starting..." : "Generate timetable"}
        </button>
      </div>
      <div className={hintClass}>
        Select a dataset or use the latest one, and set generations (default: 200).
      </div>
    </div>
  );
}

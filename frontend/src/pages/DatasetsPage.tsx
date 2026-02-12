import { useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { downloadDatasetExcel, listDatasets, uploadDatasetExcel } from "../api/datasets";
import type { Dataset } from "../types/api";
import { formatDateTime } from "../utils/format";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [createError, setCreateError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);

  const loadDatasets = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await listDatasets();
      setDatasets(data);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to load datasets.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDatasets();
  }, []);

  const handleCreate = async (event: React.FormEvent) => {
    event.preventDefault();
    setCreateError(null);

    if (!name.trim()) {
      setCreateError("Dataset name is required.");
      return;
    }

    if (!file) {
      setCreateError("Please select an .xlsx file.");
      return;
    }

    const lowered = file.name.toLowerCase();
    if (!lowered.endsWith(".xlsx")) {
      setCreateError("Only .xlsx files are supported.");
      return;
    }

    try {
      await uploadDatasetExcel(name.trim(), file);
      setName("");
      setFile(null);
      loadDatasets();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to create dataset.";
      setCreateError(message);
    }
  };

  const handleDownload = async (dataset: Dataset) => {
    try {
      setDownloadError(null);
      setDownloadingId(dataset.id);
      const blob = await downloadDatasetExcel(dataset.id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `dataset_${dataset.id}.xlsx`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to download dataset.";
      setDownloadError(message);
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <h1>Datasets</h1>
          <p>Inspect available datasets or create a new one.</p>
        </div>
      </div>

      <div className="panel" style={{ animationDelay: "0.05s" }}>
        <div className="panel-title">Create dataset</div>
        <form className="form-stack" onSubmit={handleCreate}>
          <label className="field">
            <span>Name</span>
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="dataset name"
            />
          </label>
          <label className="field">
            <span>Dataset file (.xlsx)</span>
            <input
              type="file"
              accept=".xlsx"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </label>
          {createError && <div className="inline-error">{createError}</div>}
          <button className="primary" type="submit">
            Upload dataset
          </button>
        </form>
      </div>

      <div className="panel" style={{ animationDelay: "0.1s" }}>
        <div className="panel-title">Available datasets</div>
        {error && <div className="inline-error">{error}</div>}
        {downloadError && <div className="inline-error">{downloadError}</div>}
        {isLoading ? (
          <div className="hint">Loading datasets...</div>
        ) : datasets.length === 0 ? (
          <div className="hint">No datasets yet.</div>
        ) : (
          <div className="table">
            <div className="table-header">
              <span>ID</span>
              <span>Name</span>
              <span>Created</span>
              <span>Actions</span>
            </div>
            {datasets.map((dataset) => (
              <div className="table-row" key={dataset.id}>
                <span>{dataset.id}</span>
                <span>{dataset.name}</span>
                <span>{formatDateTime(dataset.created_at)}</span>
                <span>
                  <button
                    className="inline-flex items-center gap-2 rounded-lg border-[1.5px] border-border bg-surface-strong px-4 py-2 font-medium text-sm text-text transition-all duration-200 hover:border-accent hover:-translate-y-0.5 hover:shadow-[0_4px_12px_rgba(15,118,110,0.15)] disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none"
                    type="button"
                    onClick={() => handleDownload(dataset)}
                    disabled={downloadingId === dataset.id}
                  >
                    {downloadingId === dataset.id ? (
                      "Downloading..."
                    ) : (
                      <>
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          width="18"
                          height="18"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <path d="M12 15V3" />
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                          <path d="m7 10 5 5 5-5" />
                        </svg>
                        Download
                      </>
                    )}
                  </button>
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

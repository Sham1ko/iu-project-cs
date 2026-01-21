import { useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { createDataset, listDatasets } from "../api/datasets";
import type { Dataset } from "../types/api";
import { formatDateTime } from "../utils/format";
import { safeJsonParse } from "../utils/json";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [payload, setPayload] = useState("{}");
  const [createError, setCreateError] = useState<string | null>(null);

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

    const parsed = safeJsonParse(payload);
    if (!parsed.ok) {
      setCreateError(parsed.error);
      return;
    }

    try {
      await createDataset({ name: name.trim(), payload: parsed.value });
      setName("");
      setPayload("{}");
      loadDatasets();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to create dataset.";
      setCreateError(message);
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
            <span>Payload (JSON)</span>
            <textarea
              rows={6}
              value={payload}
              onChange={(event) => setPayload(event.target.value)}
            />
          </label>
          {createError && <div className="inline-error">{createError}</div>}
          <button className="primary" type="submit">
            Create dataset
          </button>
        </form>
      </div>

      <div className="panel" style={{ animationDelay: "0.1s" }}>
        <div className="panel-title">Available datasets</div>
        {error && <div className="inline-error">{error}</div>}
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
            </div>
            {datasets.map((dataset) => (
              <div className="table-row" key={dataset.id}>
                <span>{dataset.id}</span>
                <span>{dataset.name}</span>
                <span>{formatDateTime(dataset.created_at)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

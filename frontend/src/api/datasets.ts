import { request } from "./client";
import type { Dataset, DatasetCreate } from "../types/api";

export const listDatasets = async () => {
  return request<Dataset[]>("/datasets");
};

export const createDataset = async (payload: DatasetCreate) => {
  return request<Dataset>("/datasets", {
    method: "POST",
    body: payload,
  });
};

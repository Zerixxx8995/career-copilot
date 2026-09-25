import { http } from "./httpClient";
import type { JobSummary, JobDetail } from "@/types";

export interface JobListResponse {
  jobs: JobSummary[];
  total: number;
}

export async function listJobs(params?: {
  role?: string;
  location?: string;
  limit?: number;
}): Promise<JobListResponse> {
  const qs = new URLSearchParams();
  if (params?.role) qs.set("role", params.role);
  if (params?.location) qs.set("location", params.location);
  if (params?.limit) qs.set("limit", String(params.limit));
  const query = qs.toString() ? `?${qs}` : "";
  return http.get<JobListResponse>(`/jobs${query}`);
}

export async function getJob(jobId: string): Promise<JobDetail> {
  return http.get<JobDetail>(`/jobs/${jobId}`);
}

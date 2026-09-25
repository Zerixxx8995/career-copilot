import { http } from "./httpClient";
import type { FeedbackAction } from "@/types";

export interface FeedbackResponse {
  status: string;
  updated_preference_weights: Record<string, number>;
}

export async function submitFeedback(
  jobId: string,
  action: FeedbackAction
): Promise<FeedbackResponse> {
  return http.post<FeedbackResponse>("/feedback", { job_id: jobId, action });
}

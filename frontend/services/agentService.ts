import { http } from "./httpClient";
import type { AgentQueryResponse, AgentTrace } from "@/types";

export async function submitQuery(query: string): Promise<AgentQueryResponse> {
  return http.post<AgentQueryResponse>("/agent/query", { query });
}

export async function getTrace(traceId: string): Promise<AgentTrace> {
  return http.get<AgentTrace>(`/agent/trace/${traceId}`);
}

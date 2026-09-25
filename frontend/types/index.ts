// Types shared across the frontend

export interface Skill {
  name: string;
  status: "known" | "learning" | "gap";
}

export interface CareerProfile {
  user_id: string;
  target_roles: string[];
  target_locations: string[];
  skills: Skill[];
  preference_weights: Record<string, number>;
  resume_file_name: string;
  created_at: string;
  updated_at: string | null;
}

export interface JobSummary {
  job_id: string;
  title: string;
  company: string;
  location: string;
  role_category: string;
  short_description: string;
  relevance?: number;
  adjusted_score?: number;
}

export interface JobDetail extends JobSummary {
  full_description: string;
  requirements: string[];
  source: string;
  created_at: string;
}

export interface RequirementMatch {
  requirement: string;
  matched_via: "exact" | "embedding" | "fuzzy";
  evidence: string;
}

export interface MatchResult {
  job_id: string;
  fit_score: number;
  matched_requirements: RequirementMatch[];
  missing_requirements: string[];
  explanation: string;
}

export type FeedbackAction = "interested" | "not_interested" | "applied";

export interface AgentTraceStep {
  step: number;
  tool?: string;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  duration_ms?: number;
  type?: string;
  content?: string;
}

export interface AgentQueryResponse {
  trace_id: string;
  answer: string;
  steps_count: number;
  steps?: AgentTraceStep[];
}

export interface AgentTrace {
  trace_id: string;
  user_query: string;
  steps: AgentTraceStep[];
  final_answer: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
}

export interface SkillGap {
  skill: string;
  frequency: number;
  sample_job_ids: string[];
}

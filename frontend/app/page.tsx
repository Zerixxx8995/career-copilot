"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  BrainCircuit,
  Upload,
  LogOut,
  User,
  ChevronRight,
  Sparkles,
  AlertCircle,
} from "lucide-react";

import QueryBox from "@/components/query/QueryBox";
import AgentTraceView from "@/components/query/AgentTraceView";
import JobCard from "@/components/jobs/JobCard";
import FitScoreExplain from "@/components/jobs/FitScoreExplain";
import LoadingSpinner from "@/components/shared/LoadingSpinner";
import ErrorBoundary from "@/components/shared/ErrorBoundary";

import { submitQuery } from "@/services/agentService";
import { getProfile, uploadResume } from "@/services/profileService";
import { http } from "@/services/httpClient";
import { clearToken, getUserId } from "@/services/httpClient";

import type {
  AgentQueryResponse,
  AgentTraceStep,
  CareerProfile,
  JobSummary,
  MatchResult,
} from "@/types";

interface QueryResult {
  answer: string;
  traceId: string;
  steps: AgentTraceStep[];
  jobs: JobSummary[];
}

export default function HomePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<CareerProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [fitData, setFitData] = useState<Record<string, MatchResult>>({});
  const [openFitJobId, setOpenFitJobId] = useState<string | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Auth guard
  useEffect(() => {
    const userId = getUserId();
    if (!userId) {
      router.replace("/auth");
      return;
    }
    loadProfile();
  }, []);

  const loadProfile = async () => {
    setProfileLoading(true);
    try {
      const p = await getProfile();
      setProfile(p);
    } catch {
      // No profile yet — that's OK, user needs to upload resume first
      setProfile(null);
    } finally {
      setProfileLoading(false);
    }
  };

  const handleQuery = async (query: string) => {
    setQueryLoading(true);
    setQueryError(null);
    setQueryResult(null);
    setOpenFitJobId(null);

    try {
      const res: AgentQueryResponse = await submitQuery(query);

      // Parse any job mentions from the answer (agent returns job IDs in trace steps)
      const jobIds = extractJobIdsFromSteps(res as unknown as { steps: AgentTraceStep[] });

      setQueryResult({
        answer: res.answer,
        traceId: res.trace_id,
        steps: (res as unknown as { steps: AgentTraceStep[] }).steps || [],
        jobs: jobIds.map((id) => ({ job_id: id } as JobSummary)),
      });

      // Load fit data for jobs found in trace
      for (const jobId of jobIds.slice(0, 5)) {
        fetchFitForJob(jobId);
      }
    } catch (err) {
      setQueryError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setQueryLoading(false);
    }
  };

  const fetchFitForJob = useCallback(async (jobId: string) => {
    try {
      const fit = await http.get<MatchResult>(`/jobs/${jobId}/match`);
      setFitData((prev) => ({ ...prev, [jobId]: fit }));
    } catch {
      // Not critical — fit data is optional
    }
  }, []);

  const handleViewFit = (jobId: string) => {
    setOpenFitJobId(openFitJobId === jobId ? null : jobId);
  };

  const handleFeedback = (_jobId: string, _action: string) => {
    // Preference weights updated server-side; no client state needed
  };

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadLoading(true);
    setUploadError(null);
    try {
      await uploadResume(file);
      await loadProfile();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploadLoading(false);
    }
  };

  const handleLogout = () => {
    clearToken();
    router.replace("/auth");
  };

  // Extract job IDs from agent trace steps
  const extractJobIdsFromSteps = (res: { steps?: AgentTraceStep[] }): string[] => {
    const ids = new Set<string>();
    for (const step of res.steps || []) {
      if (step.output && typeof step.output === "object") {
        const out = step.output as Record<string, unknown>;
        // search_jobs output
        const jobs = (out.jobs as JobSummary[]) || [];
        for (const j of jobs) {
          if (j?.job_id) ids.add(j.job_id);
        }
        // match_resume_to_job output
        if (out.job_id) ids.add(out.job_id as string);
        if (out.fit_score !== undefined) {
          const fit = out as unknown as MatchResult;
          if (fit.job_id) ids.add(fit.job_id);
        }
      }
    }
    return Array.from(ids);
  };

  // Build enriched jobs list from trace
  const enrichedJobs: JobSummary[] = (queryResult?.steps || []).flatMap((step) => {
    if (!step.output || typeof step.output !== "object") return [];
    const out = step.output as Record<string, unknown>;
    const jobs = (out.jobs as JobSummary[]) || [];
    return jobs.filter((j) => j?.job_id && j?.title);
  });

  return (
    <div className="min-h-dvh flex flex-col">
      {/* ── Nav ─────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-20 border-b border-white/[0.04] backdrop-blur-xl bg-[#0a0a0f]/80">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <BrainCircuit size={22} className="text-violet-400" />
            <span className="font-bold text-sm tracking-tight text-white">Career Copilot</span>
          </div>

          <nav className="flex items-center gap-1">
            <Link href="/" className="nav-link active">
              Agent
            </Link>
            <Link href="/trace" className="nav-link">
              Traces
            </Link>

            {/* Resume upload */}
            <label
              htmlFor="resume-upload"
              className="nav-link cursor-pointer flex items-center gap-1.5"
              title="Upload Resume"
            >
              {uploadLoading ? (
                <span className="text-xs text-violet-400 animate-pulse">Uploading…</span>
              ) : (
                <>
                  <Upload size={13} />
                  <span>Resume</span>
                </>
              )}
            </label>
            <input
              id="resume-upload"
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={handleResumeUpload}
            />

            {profile && (
              <span className="nav-link flex items-center gap-1.5 text-emerald-400">
                <User size={12} />
                <span className="max-w-[100px] truncate">{profile.resume_file_name || "Profile"}</span>
              </span>
            )}

            <button
              onClick={handleLogout}
              className="nav-link flex items-center gap-1"
              id="logout-btn"
              title="Log out"
            >
              <LogOut size={13} />
            </button>
          </nav>
        </div>
      </header>

      <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-8 flex flex-col gap-6">
        {/* ── Hero ──────────────────────────────────────────────── */}
        {!queryResult && !queryLoading && (
          <div className="text-center py-12 animate-fade-in">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-300 text-xs font-medium mb-6">
              <Sparkles size={11} />
              Powered by Gemini + LangGraph
            </div>
            <h1 className="text-4xl font-bold text-white mb-3 tracking-tight">
              Find roles you actually <span className="text-violet-400">fit</span>
            </h1>
            <p className="text-gray-400 text-base max-w-lg mx-auto">
              The agent searches jobs, scores your resume against each, aggregates skill
              gaps, and improves with every piece of feedback you give.
            </p>
          </div>
        )}

        {/* ── Upload prompt ─────────────────────────────────────── */}
        {!profileLoading && !profile && (
          <div className="answer-card flex items-center gap-4 animate-fade-in">
            <AlertCircle size={20} className="text-amber-400 shrink-0" />
            <div className="flex-1">
              <p className="text-sm text-amber-300 font-medium">Upload your resume to get started</p>
              <p className="text-xs text-gray-400 mt-0.5">
                The agent needs your profile to score fit and identify gaps.
              </p>
            </div>
            <label
              htmlFor="resume-upload-hero"
              className="shrink-0 feedback-btn feedback-btn-applied cursor-pointer"
            >
              <Upload size={13} />
              <span>Upload PDF</span>
            </label>
            <input
              id="resume-upload-hero"
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={handleResumeUpload}
            />
          </div>
        )}

        {uploadError && (
          <div className="flex items-center gap-2 text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3 animate-fade-in">
            <AlertCircle size={14} />
            {uploadError}
          </div>
        )}

        {/* ── Query box ─────────────────────────────────────────── */}
        <ErrorBoundary>
          <QueryBox onSubmit={handleQuery} isLoading={queryLoading} />
        </ErrorBoundary>

        {/* ── Loading ───────────────────────────────────────────── */}
        {queryLoading && (
          <div className="animate-fade-in">
            <LoadingSpinner text="Agent is thinking… (searching → matching → analysing gaps)" size="lg" />
          </div>
        )}

        {/* ── Error ─────────────────────────────────────────────── */}
        {queryError && (
          <div className="flex items-center gap-2 text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3 animate-fade-in">
            <AlertCircle size={14} />
            {queryError}
          </div>
        )}

        {/* ── Results ───────────────────────────────────────────── */}
        {queryResult && !queryLoading && (
          <div className="space-y-6 animate-slide-in">
            {/* Answer */}
            <div className="answer-card">
              <div className="flex items-center gap-2 mb-3">
                <BrainCircuit size={15} className="text-violet-400" />
                <span className="text-xs font-semibold text-violet-300 uppercase tracking-wider">
                  Agent Answer
                </span>
              </div>
              <p className="answer-text">{queryResult.answer}</p>
            </div>

            {/* Trace */}
            {queryResult.steps.length > 0 && (
              <AgentTraceView steps={queryResult.steps} traceId={queryResult.traceId} />
            )}

            {/* Job cards */}
            {enrichedJobs.length > 0 && (
              <div>
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <ChevronRight size={14} />
                  Jobs Found ({enrichedJobs.length})
                </h2>
                <div className="space-y-3 stagger">
                  {enrichedJobs.map((job) => (
                    <div key={job.job_id}>
                      <JobCard
                        job={job}
                        fitScore={fitData[job.job_id]?.fit_score}
                        onFeedback={handleFeedback}
                        onViewFit={handleViewFit}
                      />
                      {openFitJobId === job.job_id && fitData[job.job_id] && (
                        <div className="mt-2 ml-2 animate-fade-in">
                          <FitScoreExplain match={fitData[job.job_id]} />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

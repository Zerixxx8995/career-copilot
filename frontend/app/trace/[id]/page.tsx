"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { BrainCircuit, ArrowLeft, Clock, ChevronDown, ChevronUp, Wrench, CheckCircle } from "lucide-react";
import { getTrace } from "@/services/agentService";
import LoadingSpinner from "@/components/shared/LoadingSpinner";
import type { AgentTrace, AgentTraceStep } from "@/types";
import { getUserId } from "@/services/httpClient";

const TOOL_COLORS: Record<string, string> = {
  search_jobs: "text-blue-400 bg-blue-400/10 border-blue-400/20",
  get_job_details: "text-cyan-400 bg-cyan-400/10 border-cyan-400/20",
  match_resume_to_job: "text-violet-400 bg-violet-400/10 border-violet-400/20",
  identify_skill_gaps: "text-amber-400 bg-amber-400/10 border-amber-400/20",
  save_feedback: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
};

function FullTraceStep({ step, index }: { step: AgentTraceStep; index: number }) {
  const [open, setOpen] = useState(true);
  const colorClass = TOOL_COLORS[step.tool || ""] || "text-gray-400 bg-gray-400/10 border-gray-400/20";

  if (step.type === "final_answer") {
    return (
      <div className="trace-step final p-4">
        <div className="flex items-center gap-2 mb-2">
          <CheckCircle size={15} className="text-emerald-400" />
          <span className="text-sm font-semibold text-emerald-400">Final Answer</span>
        </div>
        <p className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">{step.content}</p>
      </div>
    );
  }

  return (
    <div className="trace-step">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 text-left"
      >
        <span className="trace-step-number shrink-0">{index + 1}</span>
        <span className={`trace-tool-badge border shrink-0 ${colorClass}`}>
          <Wrench size={11} className="inline mr-1" />
          {step.tool}
        </span>
        {step.duration_ms && (
          <span className="flex items-center gap-1 text-xs text-gray-500">
            <Clock size={11} /> {step.duration_ms}ms
          </span>
        )}
        <span className="ml-auto">
          {open ? <ChevronUp size={14} className="text-gray-500" /> : <ChevronDown size={14} className="text-gray-500" />}
        </span>
      </button>

      {open && (
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1.5">Input</p>
            <pre className="trace-json">{JSON.stringify(step.input, null, 2)}</pre>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1.5">Output</p>
            <pre className="trace-json">{JSON.stringify(step.output, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default function TracePage() {
  const params = useParams();
  const router = useRouter();
  const traceId = params.id as string;
  const [trace, setTrace] = useState<AgentTrace | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getUserId()) { router.replace("/auth"); return; }
    fetchTrace();
  }, [traceId]);

  const fetchTrace = async () => {
    setLoading(true);
    try {
      const t = await getTrace(traceId);
      setTrace(t);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load trace");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-20 border-b border-white/[0.04] backdrop-blur-xl bg-[#0a0a0f]/80">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center gap-4">
          <Link href="/" className="flex items-center gap-1.5 text-gray-400 hover:text-white transition-colors text-sm">
            <ArrowLeft size={15} />
            Back
          </Link>
          <div className="flex items-center gap-2 ml-2">
            <BrainCircuit size={16} className="text-violet-400" />
            <span className="font-semibold text-sm text-white">Agent Trace</span>
          </div>
          <span className="ml-auto text-xs font-mono text-gray-500">{traceId}</span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {loading && <LoadingSpinner text="Loading trace…" />}

        {error && (
          <div className="text-center py-16 text-red-400">
            <p className="font-medium">{error}</p>
            <Link href="/" className="text-sm text-violet-400 hover:underline mt-2 inline-block">
              Back to Agent
            </Link>
          </div>
        )}

        {trace && (
          <div className="space-y-6 animate-fade-in">
            {/* Header info */}
            <div className="answer-card">
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Query</p>
              <p className="text-white font-medium">{trace.user_query}</p>
              <p className="text-xs text-gray-600 mt-2">
                {new Date(trace.created_at).toLocaleString()}
                {" · "}{trace.steps.filter(s => s.tool).length} tool calls
              </p>
            </div>

            {/* Steps */}
            <div>
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Reasoning Steps
              </h2>
              <div className="space-y-3">
                {trace.steps.map((step, i) => (
                  <FullTraceStep key={i} step={step} index={i} />
                ))}
              </div>
            </div>

            {/* Final answer */}
            {trace.final_answer && (
              <div className="answer-card">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle size={15} className="text-emerald-400" />
                  <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Final Answer</span>
                </div>
                <p className="answer-text">{trace.final_answer}</p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Clock, Wrench, CheckCircle } from "lucide-react";
import type { AgentTraceStep } from "@/types";

interface AgentTraceViewProps {
  steps: AgentTraceStep[];
  traceId: string;
}

const TOOL_COLORS: Record<string, string> = {
  search_jobs: "text-blue-400 bg-blue-400/10 border-blue-400/20",
  get_job_details: "text-cyan-400 bg-cyan-400/10 border-cyan-400/20",
  match_resume_to_job: "text-violet-400 bg-violet-400/10 border-violet-400/20",
  identify_skill_gaps: "text-amber-400 bg-amber-400/10 border-amber-400/20",
  save_feedback: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
};

function ToolStep({ step, index }: { step: AgentTraceStep; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const colorClass = TOOL_COLORS[step.tool || ""] || "text-gray-400 bg-gray-400/10 border-gray-400/20";

  if (step.type === "final_answer") {
    return (
      <div className="trace-step final">
        <div className="flex items-center gap-2">
          <CheckCircle size={16} className="text-emerald-400" />
          <span className="text-sm font-medium text-emerald-400">Final Answer Generated</span>
        </div>
      </div>
    );
  }

  return (
    <div className="trace-step">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between gap-3 text-left"
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="trace-step-number">{index + 1}</span>
          <span className={`trace-tool-badge border ${colorClass}`}>
            <Wrench size={11} className="inline mr-1" />
            {step.tool}
          </span>
          {step.duration_ms && (
            <span className="flex items-center gap-1 text-xs text-gray-500">
              <Clock size={11} />
              {step.duration_ms}ms
            </span>
          )}
        </div>
        {expanded ? (
          <ChevronUp size={14} className="text-gray-500 shrink-0" />
        ) : (
          <ChevronDown size={14} className="text-gray-500 shrink-0" />
        )}
      </button>

      {expanded && (
        <div className="mt-3 space-y-2">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Input</p>
            <pre className="trace-json">{JSON.stringify(step.input, null, 2)}</pre>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Output</p>
            <pre className="trace-json">{JSON.stringify(step.output, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AgentTraceView({ steps, traceId }: AgentTraceViewProps) {
  const [open, setOpen] = useState(false);
  const toolSteps = steps.filter((s) => s.tool || s.type === "final_answer");

  return (
    <div className="agent-trace-container">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200 transition-colors w-full"
        id="trace-toggle-btn"
        aria-expanded={open}
      >
        <span className="trace-id-badge">{toolSteps.length} steps</span>
        <span>Agent reasoning trace</span>
        <span className="text-xs text-gray-600 ml-auto font-mono">{traceId.slice(0, 8)}…</span>
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {open && (
        <div className="mt-3 space-y-2">
          {toolSteps.map((step, i) => (
            <ToolStep key={i} step={step} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}

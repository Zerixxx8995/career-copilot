"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { BrainCircuit, ArrowLeft, Clock, ChevronRight } from "lucide-react";
import { http } from "@/services/httpClient";
import { getUserId } from "@/services/httpClient";
import LoadingSpinner from "@/components/shared/LoadingSpinner";

interface TraceSummary {
  trace_id: string;
  user_query: string;
  steps_count: number;
  created_at: string;
}

export default function TracesListPage() {
  const router = useRouter();
  const [traces, setTraces] = useState<TraceSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getUserId()) { router.replace("/auth"); return; }
    fetchTraces();
  }, []);

  const fetchTraces = async () => {
    try {
      const res = await http.get<{ traces: TraceSummary[] }>("/agent/traces");
      setTraces(res.traces || []);
    } catch {
      setTraces([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-20 border-b border-white/[0.04] backdrop-blur-xl bg-[#0a0a0f]/80">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center gap-4">
          <Link href="/" className="flex items-center gap-1.5 text-gray-400 hover:text-white transition-colors text-sm">
            <ArrowLeft size={15} /> Back
          </Link>
          <div className="flex items-center gap-2 ml-2">
            <BrainCircuit size={16} className="text-violet-400" />
            <span className="font-semibold text-sm text-white">Agent Traces</span>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {loading ? (
          <LoadingSpinner text="Loading traces…" />
        ) : traces.length === 0 ? (
          <div className="text-center py-20 text-gray-500">
            <BrainCircuit size={36} className="mx-auto mb-4 opacity-30" />
            <p>No traces yet. Run a query to see agent reasoning here.</p>
            <Link href="/" className="text-violet-400 hover:underline text-sm mt-3 inline-block">
              Go to Agent
            </Link>
          </div>
        ) : (
          <div className="space-y-2 stagger">
            {traces.map((t) => (
              <Link
                key={t.trace_id}
                href={`/trace/${t.trace_id}`}
                className="flex items-center gap-4 job-card hover:no-underline group"
                id={`trace-link-${t.trace_id}`}
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white font-medium line-clamp-1">{t.user_query}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                      <Clock size={10} />
                      {new Date(t.created_at).toLocaleString()}
                    </span>
                    <span className="trace-id-badge">{t.steps_count} steps</span>
                  </div>
                </div>
                <ChevronRight size={15} className="text-gray-600 group-hover:text-violet-400 transition-colors shrink-0" />
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

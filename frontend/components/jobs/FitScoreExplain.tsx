"use client";

import { CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import type { MatchResult } from "@/types";

interface FitScoreExplainProps {
  match: MatchResult;
}

const METHOD_LABELS: Record<string, { label: string; cls: string }> = {
  exact: { label: "exact", cls: "badge-exact" },
  embedding: { label: "semantic", cls: "badge-semantic" },
  fuzzy: { label: "fuzzy", cls: "badge-fuzzy" },
};

export default function FitScoreExplain({ match }: FitScoreExplainProps) {
  const pct = Math.round(match.fit_score * 100);
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  const ringColor =
    pct >= 75 ? "#34d399" : pct >= 50 ? "#fbbf24" : "#f87171";

  return (
    <div className="fit-explain-card">
      {/* Score ring */}
      <div className="flex items-center gap-5 mb-5">
        <div className="relative w-24 h-24 shrink-0">
          <svg viewBox="0 0 88 88" className="w-full h-full -rotate-90">
            <circle cx="44" cy="44" r={radius} fill="none" stroke="#ffffff10" strokeWidth="8" />
            <circle
              cx="44" cy="44" r={radius}
              fill="none"
              stroke={ringColor}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              style={{ transition: "stroke-dashoffset 0.8s ease" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-bold text-white">{pct}%</span>
            <span className="text-xs text-gray-400">fit</span>
          </div>
        </div>
        <div>
          <p className="text-sm text-gray-300 leading-relaxed">{match.explanation}</p>
        </div>
      </div>

      {/* Matched requirements */}
      {match.matched_requirements.length > 0 && (
        <div className="mb-4">
          <h4 className="fit-section-title text-emerald-400">
            <CheckCircle2 size={14} />
            Matched ({match.matched_requirements.length})
          </h4>
          <ul className="space-y-1.5">
            {match.matched_requirements.map((r, i) => {
              const badge = METHOD_LABELS[r.matched_via] || { label: r.matched_via, cls: "" };
              return (
                <li key={i} className="fit-requirement-row matched">
                  <CheckCircle2 size={13} className="text-emerald-400 shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-200 flex-1">{r.requirement}</span>
                  <span className={`method-badge ${badge.cls}`}>{badge.label}</span>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {/* Missing requirements */}
      {match.missing_requirements.length > 0 && (
        <div>
          <h4 className="fit-section-title text-red-400">
            <XCircle size={14} />
            Missing ({match.missing_requirements.length})
          </h4>
          <ul className="space-y-1.5">
            {match.missing_requirements.map((r, i) => (
              <li key={i} className="fit-requirement-row missing">
                <AlertCircle size={13} className="text-red-400 shrink-0 mt-0.5" />
                <span className="text-sm text-gray-300">{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

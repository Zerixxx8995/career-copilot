"use client";

import { Building2, MapPin, Tag, TrendingUp } from "lucide-react";
import type { JobSummary } from "@/types";
import FeedbackButtons from "./FeedbackButtons";

interface JobCardProps {
  job: JobSummary;
  fitScore?: number;
  onFeedback?: (jobId: string, action: string) => void;
  onViewFit?: (jobId: string) => void;
  compact?: boolean;
}

function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 75
      ? "score-high"
      : pct >= 50
      ? "score-mid"
      : "score-low";
  return (
    <div className={`score-badge ${color}`}>
      <TrendingUp size={12} />
      <span>{pct}% fit</span>
    </div>
  );
}

export default function JobCard({
  job,
  fitScore,
  onFeedback,
  onViewFit,
  compact = false,
}: JobCardProps) {
  return (
    <div className="job-card group" id={`job-card-${job.job_id}`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0">
          <h3 className="job-title line-clamp-1">{job.title}</h3>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1">
            <span className="job-meta-item">
              <Building2 size={12} />
              {job.company}
            </span>
            <span className="job-meta-item">
              <MapPin size={12} />
              {job.location}
            </span>
            <span className="job-meta-item">
              <Tag size={12} />
              {job.role_category}
            </span>
          </div>
        </div>
        {fitScore !== undefined && <ScoreBadge score={fitScore} />}
      </div>

      {/* Description */}
      {!compact && (
        <p className="job-description line-clamp-2">{job.short_description}</p>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-white/5">
        {onViewFit && (
          <button
            onClick={() => onViewFit(job.job_id)}
            className="view-fit-btn"
            id={`view-fit-${job.job_id}`}
          >
            View Fit Analysis
          </button>
        )}
        {onFeedback && (
          <FeedbackButtons
            jobId={job.job_id}
            onFeedback={onFeedback}
          />
        )}
      </div>
    </div>
  );
}

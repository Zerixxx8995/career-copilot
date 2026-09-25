"use client";

import { useState } from "react";
import { Heart, X, Send, Loader2 } from "lucide-react";
import { submitFeedback } from "@/services/feedbackService";
import type { FeedbackAction } from "@/types";

interface FeedbackButtonsProps {
  jobId: string;
  onFeedback?: (jobId: string, action: FeedbackAction) => void;
}

const ACTIONS: { id: FeedbackAction; label: string; icon: React.ReactNode; cls: string }[] = [
  {
    id: "interested",
    label: "Interested",
    icon: <Heart size={13} />,
    cls: "feedback-btn-interested",
  },
  {
    id: "applied",
    label: "Applied",
    icon: <Send size={13} />,
    cls: "feedback-btn-applied",
  },
  {
    id: "not_interested",
    label: "Pass",
    icon: <X size={13} />,
    cls: "feedback-btn-pass",
  },
];

export default function FeedbackButtons({ jobId, onFeedback }: FeedbackButtonsProps) {
  const [selected, setSelected] = useState<FeedbackAction | null>(null);
  const [loading, setLoading] = useState<FeedbackAction | null>(null);

  const handleFeedback = async (action: FeedbackAction) => {
    if (loading || selected) return;
    setLoading(action);
    try {
      await submitFeedback(jobId, action);
      setSelected(action);
      onFeedback?.(jobId, action);
    } catch (err) {
      console.error("Feedback error:", err);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="flex gap-1.5" role="group" aria-label="Job feedback">
      {ACTIONS.map((a) => (
        <button
          key={a.id}
          onClick={() => handleFeedback(a.id)}
          disabled={!!loading || !!selected}
          id={`feedback-${a.id}-${jobId}`}
          className={`feedback-btn ${a.cls} ${
            selected === a.id ? "opacity-100 ring-1 ring-white/20" : ""
          } ${selected && selected !== a.id ? "opacity-30" : ""}`}
          aria-pressed={selected === a.id}
          title={a.label}
        >
          {loading === a.id ? (
            <Loader2 size={13} className="animate-spin" />
          ) : (
            a.icon
          )}
          <span className="hidden sm:inline">{a.label}</span>
        </button>
      ))}
    </div>
  );
}

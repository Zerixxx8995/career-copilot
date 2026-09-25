"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Zap } from "lucide-react";

interface QueryBoxProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

const EXAMPLE_QUERIES = [
  "Find ML roles in Bengaluru I'd be a good fit for",
  "What skills am I missing across the top ML jobs?",
  "Show me backend engineering roles and rate my fit",
  "Which of my projects shows the most relevant experience?",
];

export default function QueryBox({ onSubmit, isLoading }: QueryBoxProps) {
  const [query, setQuery] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [query]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    onSubmit(query.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="relative">
        <div className="query-box-container group">
          <textarea
            ref={textareaRef}
            id="agent-query-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask the agent anything about your career fit…"
            rows={1}
            disabled={isLoading}
            className="query-textarea"
            aria-label="Career query input"
          />
          <button
            type="submit"
            id="agent-query-submit"
            disabled={!query.trim() || isLoading}
            className="query-submit-btn"
            aria-label="Submit query"
          >
            {isLoading ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <Send size={18} />
            )}
          </button>
        </div>
      </form>

      {/* Example queries */}
      <div className="mt-4 flex flex-wrap gap-2">
        {EXAMPLE_QUERIES.map((q) => (
          <button
            key={q}
            onClick={() => {
              setQuery(q);
              textareaRef.current?.focus();
            }}
            className="example-chip"
            disabled={isLoading}
          >
            <Zap size={12} className="inline mr-1 text-violet-400" />
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

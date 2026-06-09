"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import type { TriageData } from "@/lib/types";

export function TriageCard({ data }: { data: TriageData }) {
  const [expanded, setExpanded] = useState(false);

  const diffColor =
    data.difficulty_score <= 3 ? "bg-emerald-500" : data.difficulty_score <= 7 ? "bg-amber-500" : "bg-rose-500";
  const fixColor =
    data.fixability_score >= 7 ? "bg-emerald-500" : data.fixability_score >= 4 ? "bg-amber-500" : "bg-rose-500";

  return (
    <div className="rounded-md border border-line bg-white p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase text-ink/70">Issue Triage</h3>
        <div className="flex gap-2">
          {data.good_first_issue && (
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-700">
              Good First Issue
            </span>
          )}
          <span
            className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
              data.contributor_level === "beginner"
                ? "bg-emerald-100 text-emerald-700"
                : data.contributor_level === "intermediate"
                ? "bg-amber-100 text-amber-700"
                : "bg-rose-100 text-rose-700"
            }`}
          >
            {data.contributor_level}
          </span>
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <div className="mb-1 flex justify-between text-xs font-medium text-ink/60">
            <span>Difficulty</span>
            <span>{data.difficulty_score} / 10</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-panel">
            <div
              className={`h-full ${diffColor} transition-all`}
              style={{ width: `${(data.difficulty_score / 10) * 100}%` }}
            />
          </div>
        </div>

        <div>
          <div className="mb-1 flex justify-between text-xs font-medium text-ink/60">
            <span>Fixability</span>
            <span>{data.fixability_score} / 10</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-panel">
            <div
              className={`h-full ${fixColor} transition-all`}
              style={{ width: `${(data.fixability_score / 10) * 100}%` }}
            />
          </div>
        </div>
      </div>

      <div className="rounded-md border border-line bg-panel overflow-hidden">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex w-full items-center justify-between px-3 py-2 text-xs font-semibold text-ink/70 hover:bg-ink/5"
        >
          <span>Triage Reasoning</span>
          {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        </button>
        {expanded && (
          <div className="border-t border-line px-3 py-2 text-xs leading-relaxed text-ink/80">
            {data.triage_reasoning}
          </div>
        )}
      </div>
    </div>
  );
}

"use client";

import { FileCode2, GitPullRequestDraft, ShieldAlert, TestTube2 } from "lucide-react";
import { useState } from "react";
import clsx from "clsx";
import type { WorkflowPlanResponse } from "@/lib/types";

const tabs = ["Summary", "Files", "Tests", "Security", "Audit"] as const;

export function ReviewDashboard({ result }: { result: WorkflowPlanResponse | null }) {
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]>("Summary");

  if (!result) {
    return (
      <section className="flex min-h-80 items-center justify-center border-l border-line bg-panel p-6 text-sm text-ink/60">
        Awaiting workflow output
      </section>
    );
  }

  return (
    <section className="border-t border-line bg-white xl:border-l xl:border-t-0">
      <div className="flex h-14 items-center justify-between border-b border-line px-4">
        <div className="min-w-0">
          <h2 className="truncate text-sm font-semibold">Review report</h2>
          <p className="truncate text-xs text-ink/60">{result.workflow_id}</p>
        </div>
        <GitPullRequestDraft aria-hidden className="h-5 w-5 text-pine" />
      </div>

      <div className="grid grid-cols-4 border-b border-line">
        {tabs.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={clsx(
              "h-10 border-r border-line px-2 text-xs font-medium last:border-r-0",
              activeTab === tab ? "bg-mint text-pine" : "bg-white text-ink/65 hover:bg-panel"
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="scrollbar-thin max-h-[44rem] overflow-auto p-4 xl:h-[calc(100vh-7rem)] xl:max-h-none">
        {activeTab === "Summary" && (
          <div className="space-y-4">
            <MetricRow
              icon={<FileCode2 aria-hidden className="h-4 w-4" />}
              label="Difficulty"
              value={`${result.difficulty.level} - ${result.difficulty.estimated_work}`}
            />
            <MetricRow
              icon={<ShieldAlert aria-hidden className="h-4 w-4" />}
              label="Confidence"
              value={`${Math.round(result.difficulty.confidence * 100)}%`}
            />
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase text-ink/50">Root cause</h3>
              <p className="rounded-md border border-line bg-panel p-3 text-sm leading-6">{result.plan.root_cause}</p>
            </div>
            <ListBlock title="Plan" items={result.plan.proposed_steps} />
            <ListBlock title="Mentor mode" items={result.mentor.possible_solutions} />
          </div>
        )}

        {activeTab === "Files" && (
          <div className="space-y-4">
            <ListBlock title="Inspect" items={result.plan.files_to_inspect} empty="No files selected yet" />
            <ListBlock title="Likely changed" items={result.plan.files_likely_changed} empty="No changes generated yet" />
            <ListBlock title="Repository risks" items={result.plan.risks} />
          </div>
        )}

        {activeTab === "Tests" && (
          <div className="space-y-4">
            <MetricRow icon={<TestTube2 aria-hidden className="h-4 w-4" />} label="Status" value="Pending approval" />
            <ListBlock title="Commands" items={result.plan.tests_to_run} />
          </div>
        )}

        {activeTab === "Security" && (
          <div className="space-y-4">
            <MetricRow icon={<ShieldAlert aria-hidden className="h-4 w-4" />} label="Score" value="Pending scan" />
            <ListBlock title="Checks" items={["Secrets", "Path traversal", "Command injection", "SQL injection", "Auth boundaries"]} />
          </div>
        )}

        {activeTab === "Audit" && (
          <div className="space-y-2">
            {result.audit_events.map((event, index) => (
              <pre key={index} className="overflow-auto rounded-md border border-line bg-panel p-3 text-xs leading-5">
                {JSON.stringify(event, null, 2)}
              </pre>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function MetricRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-line bg-panel px-3 py-2">
      <div className="flex min-w-0 items-center gap-2 text-sm text-ink/70">
        <span className="text-pine">{icon}</span>
        <span className="truncate">{label}</span>
      </div>
      <span className="truncate pl-3 text-sm font-semibold">{value}</span>
    </div>
  );
}

function ListBlock({ title, items, empty }: { title: string; items: string[]; empty?: string }) {
  return (
    <div>
      <h3 className="mb-2 text-xs font-semibold uppercase text-ink/50">{title}</h3>
      <ul className="divide-y divide-line rounded-md border border-line bg-white">
        {(items.length ? items : [empty ?? "None"]).map((item, index) => (
          <li key={`${item}-${index}`} className="px-3 py-2 text-sm leading-6 text-ink/80">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

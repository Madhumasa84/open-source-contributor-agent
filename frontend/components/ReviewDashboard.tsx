"use client";

import { AlertTriangle, BookOpen, FileCode2, GitPullRequestDraft, Loader2, ShieldAlert, TestTube2 } from "lucide-react";
import { useState } from "react";
import clsx from "clsx";
import type { WorkflowPlanResponse } from "@/lib/types";
import { runSecurityScan, runTests } from "@/lib/api";
import ReactDiffViewer from "react-diff-viewer-continued";

const tabs = ["Summary", "Files", "Onboarding", "Tests", "Security", "Audit", "Review"] as const;

export function ReviewDashboard({
  result,
  setResult
}: {
  result: WorkflowPlanResponse | null;
  setResult: (r: WorkflowPlanResponse | null) => void;
}) {
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]>("Summary");
  const [runningTests, setRunningTests] = useState(false);
  const [runningSecurity, setRunningSecurity] = useState(false);
  const [execError, setExecError] = useState<string | null>(null);

  if (!result) {
    return (
      <section className="flex min-h-80 items-center justify-center border-l border-line bg-panel p-6 text-sm text-ink/60">
        Awaiting workflow output
      </section>
    );
  }

  async function triggerTests() {
    if (!result) return;
    setRunningTests(true);
    setExecError(null);
    try {
      const resp = await runTests(result.workflow_id);
      setResult(resp);
      setActiveTab("Tests");
    } catch (err) {
      setExecError(err instanceof Error ? err.message : "Failed to run tests");
    } finally {
      setRunningTests(false);
    }
  }

  async function triggerSecurity() {
    if (!result) return;
    setRunningSecurity(true);
    setExecError(null);
    try {
      const resp = await runSecurityScan(result.workflow_id);
      setResult(resp);
      setActiveTab("Security");
    } catch (err) {
      setExecError(err instanceof Error ? err.message : "Failed to run security scan");
    } finally {
      setRunningSecurity(false);
    }
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

      <div className="grid grid-cols-3 sm:grid-cols-6 border-b border-line">
        {tabs.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={clsx(
              "h-10 border-r border-line px-1 text-xs font-medium last:border-r-0 truncate",
              activeTab === tab ? "bg-mint text-pine font-semibold" : "bg-white text-ink/65 hover:bg-panel"
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

        {activeTab === "Onboarding" && (
          <div className="space-y-4">
            {result.repository ? (
              <>
                <ListBlock
                  title="Build & Test Instructions"
                  items={
                    result.repository.build_systems.includes("npm")
                      ? ["npm install", "npm test", "npm run lint"]
                      : result.repository.build_systems.includes("Python packaging")
                      ? ["python -m venv .venv", "pip install -e .[dev]", "pytest"]
                      : result.repository.build_systems.includes("Docker Compose")
                      ? ["docker compose up --build"]
                      : ["Read README and dependency manifests before running commands."]
                  }
                />
                <ListBlock
                  title="Architecture Overview"
                  items={result.repository.architecture.length ? result.repository.architecture : ["Standard module layout"]}
                />
                <ListBlock
                  title="Important Modules"
                  items={result.repository.important_files.slice(0, 8)}
                />
                <ListBlock
                  title="Development Workflow"
                  items={[
                    "Create an isolated branch or worktree.",
                    "Reproduce the issue before editing code.",
                    "Add or update a focused regression test.",
                    "Run tests, linting, type checks, and security review.",
                    "Prepare a review report before any PR action."
                  ]}
                />
              </>
            ) : (
              <div className="rounded-md border border-line bg-panel p-4 text-center text-sm text-ink/60">
                Awaiting repository path analysis. Please provide a local repository path or clone an approved repository first.
              </div>
            )}
          </div>
        )}

        {activeTab === "Tests" && (
          <div className="space-y-4">
            {result.review_report?.tests_run && result.review_report.tests_run.length > 0 ? (
              <>
                <MetricRow icon={<TestTube2 aria-hidden className="h-4 w-4" />} label="Status" value="Completed Successfully" />
                <ListBlock title="Executed Test Commands" items={result.review_report.tests_run} />
              </>
            ) : (
              <>
                <MetricRow icon={<TestTube2 aria-hidden className="h-4 w-4" />} label="Status" value="Not run yet" />
                <ListBlock title="Target Commands" items={result.plan.tests_to_run} />
                {result.repository_path ? (
                  <button
                    type="button"
                    onClick={triggerTests}
                    disabled={runningTests}
                    className="flex w-full items-center justify-center gap-2 rounded-md bg-pine h-10 text-sm font-semibold text-white hover:bg-pine/90 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {runningTests && <Loader2 aria-hidden className="h-4 w-4 animate-spin" />}
                    Execute Tests
                  </button>
                ) : (
                  <div className="rounded-md border border-line bg-panel p-3 text-xs text-ink/60 text-center">
                    Repository not cloned or analyzed yet. Clone the repository first to run tests.
                  </div>
                )}
              </>
            )}
            {execError && (
              <div className="flex items-start gap-2 rounded-md border border-danger/30 bg-danger/10 p-3 text-xs text-danger">
                <AlertTriangle aria-hidden className="h-4 w-4 shrink-0 mt-0.5" />
                <span>{execError}</span>
              </div>
            )}
          </div>
        )}

        {activeTab === "Security" && (
          <div className="space-y-4">
            {result.review_report?.security_review ? (
              <>
                <MetricRow
                  icon={<ShieldAlert aria-hidden className="h-4 w-4" />}
                  label="Security Score"
                  value={`${result.review_report.security_review.score}/100`}
                />
                <div>
                  <h3 className="mb-2 text-xs font-semibold uppercase text-ink/50">Findings</h3>
                  {result.review_report.security_review.findings.length > 0 ? (
                    <ul className="divide-y divide-line rounded-md border border-line bg-white overflow-hidden">
                      {result.review_report.security_review.findings.map((finding, idx) => (
                        <li key={idx} className="p-3 text-xs leading-5">
                          <div className="flex justify-between font-semibold">
                            <span className="text-danger">{finding.rule}</span>
                            <span className="text-ink/50 uppercase">{finding.severity}</span>
                          </div>
                          <div className="mt-1 text-ink/80">{finding.message}</div>
                          <div className="mt-1 text-ink/40 font-mono">
                            {finding.file}:{finding.line}
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="rounded-md border border-line bg-panel p-4 text-center text-sm text-pine font-medium">
                      No security issues detected. Code matches standard security patterns!
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                <MetricRow icon={<ShieldAlert aria-hidden className="h-4 w-4" />} label="Status" value="Pending Scan" />
                <ListBlock title="Checks Configured" items={["Hardcoded secrets", "Path traversal", "Command injection", "SQL injection", "Auth bypasses"]} />
                {result.repository_path ? (
                  <button
                    type="button"
                    onClick={triggerSecurity}
                    disabled={runningSecurity}
                    className="flex w-full items-center justify-center gap-2 rounded-md bg-pine h-10 text-sm font-semibold text-white hover:bg-pine/90 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {runningSecurity && <Loader2 aria-hidden className="h-4 w-4 animate-spin" />}
                    Run Security Scan
                  </button>
                ) : (
                  <div className="rounded-md border border-line bg-panel p-3 text-xs text-ink/60 text-center">
                    Repository not cloned or analyzed yet. Clone the repository first to run security review.
                  </div>
                )}
              </>
            )}
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

        {activeTab === "Review" && (
          <div className="space-y-4">
            {result.patch_diff ? (
              <div className="rounded-md border border-line bg-white overflow-hidden">
                <div className="flex items-center justify-between bg-panel p-3 border-b border-line">
                  <span className="font-semibold text-sm">Patch Diff</span>
                  <div className="flex gap-2">
                    {result.patch_iterations !== null && (
                      <span className="bg-pine/10 text-pine px-2 py-0.5 rounded text-xs font-semibold">
                        Solved in {result.patch_iterations} iterations
                      </span>
                    )}
                    {result.patch_test_status && (
                      <span className={clsx(
                        "px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider",
                        result.patch_test_status === "passed" ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"
                      )}>
                        {result.patch_test_status}
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-[10px]">
                  <ReactDiffViewer oldValue="" newValue={result.patch_diff} splitView={false} />
                </div>
              </div>
            ) : (
              <div className="rounded-md border border-line bg-panel p-6 text-center text-sm text-ink/60">
                No patch generated yet.
              </div>
            )}
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

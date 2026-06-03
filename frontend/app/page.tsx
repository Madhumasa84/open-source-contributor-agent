"use client";

import { AlertCircle, Download, GitBranchPlus, Loader2, Play, RotateCcw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { ApprovalGate } from "@/components/ApprovalGate";
import { ProviderMatrix } from "@/components/ProviderMatrix";
import { ReviewDashboard } from "@/components/ReviewDashboard";
import { WorkflowRail } from "@/components/WorkflowRail";
import {
  cloneRepository,
  createWorkflowPlan,
  fetchGitHubIssue,
  fetchProviders,
  submitApproval
} from "@/lib/api";
import type {
  ApprovalStatus,
  CloneRepositoryResponse,
  GitHubIssueDetails,
  ProviderDescriptor,
  ProviderSelection,
  WorkflowPlanResponse,
  WorkflowStage
} from "@/lib/types";

const fallbackProviders: ProviderDescriptor[] = [
  {
    name: "gemini",
    configured: false,
    default_models: ["gemini-3.1-pro", "gemini-flash"],
    capabilities: { streaming: true, tool_calling: true, local: false }
  },
  {
    name: "anthropic",
    configured: false,
    default_models: ["claude-sonnet", "claude-opus"],
    capabilities: { streaming: true, tool_calling: true, local: false }
  },
  {
    name: "openrouter",
    configured: false,
    default_models: ["deepseek/deepseek-chat", "qwen/qwen3", "moonshotai/kimi"],
    capabilities: { streaming: true, tool_calling: true, local: false }
  },
  {
    name: "ollama",
    configured: true,
    default_models: ["llama3.1", "gemma2", "qwen2.5"],
    capabilities: { streaming: true, tool_calling: false, local: true }
  }
];

export default function Home() {
  const [issueUrl, setIssueUrl] = useState("https://github.com/example/project/issues/1");
  const [repositoryPath, setRepositoryPath] = useState("");
  const [issueSummary, setIssueSummary] = useState("");
  const [issueDetails, setIssueDetails] = useState<GitHubIssueDetails | null>(null);
  const [cloneUrl, setCloneUrl] = useState("https://github.com/example/project");
  const [cloneTarget, setCloneTarget] = useState("");
  const [mode, setMode] = useState<"learn" | "auto_fix">("learn");
  const [providers, setProviders] = useState<ProviderDescriptor[]>(fallbackProviders);
  const [selections, setSelections] = useState<ProviderSelection[]>([]);
  const [result, setResult] = useState<WorkflowPlanResponse | null>(null);
  const [cloneResult, setCloneResult] = useState<CloneRepositoryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [issueLoading, setIssueLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProviders()
      .then(setProviders)
      .catch(() => setProviders(fallbackProviders));
  }, []);

  const stage: WorkflowStage = result?.stage ?? "created";
  const selectedModels = useMemo(() => selections.map((item) => item.model).join(", "), [selections]);

  function buildIssueSummary(details: GitHubIssueDetails) {
    const cleaned = details.body.replace(/\s+/g, " ").trim();
    const snippet = cleaned.slice(0, 280);
    return snippet ? `${details.title}\n\n${snippet}` : details.title;
  }

  async function submit() {
    setLoading(true);
    setError(null);
    try {
      const response = await createWorkflowPlan({
        issueUrl,
        repositoryPath,
        issueSummary,
        mode,
        providers: selections
      });
      setResult(response);
      setCloneResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Workflow request failed");
    } finally {
      setLoading(false);
    }
  }

  async function loadIssueDetails() {
    if (!issueUrl.trim()) {
      return;
    }
    setIssueLoading(true);
    setError(null);
    try {
      const response = await fetchGitHubIssue(issueUrl);
      setIssueDetails(response);
      setIssueSummary((current) => (current.trim() ? current : buildIssueSummary(response)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Issue request failed");
    } finally {
      setIssueLoading(false);
    }
  }

  async function decidePlan(decision: ApprovalStatus) {
    if (!result) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const approval = await submitApproval({
        workflowId: result.workflow_id,
        gate: "plan",
        actor: "human",
        decision
      });
      setResult({
        ...result,
        approval_status: approval.status,
        stage: approval.next_stage
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval request failed");
    } finally {
      setLoading(false);
    }
  }

  async function cloneApprovedRepository() {
    if (!result) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await cloneRepository({
        workflowId: result.workflow_id,
        repositoryUrl: cloneUrl,
        approvedBy: "human",
        targetName: cloneTarget
      });
      setCloneResult(response);
      if (response.status === "completed") {
        setRepositoryPath(response.target_path);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Clone request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-panel text-ink xl:grid xl:grid-cols-[13rem_minmax(0,1fr)_26rem]">
      <WorkflowRail stage={stage} />

      <section className="min-w-0">
        <div className="flex h-14 items-center justify-between border-b border-line bg-white px-5">
          <div className="min-w-0">
            <h1 className="truncate text-base font-semibold">Open Source Contributor Agent</h1>
            <p className="truncate text-xs text-ink/60">{selectedModels || "No consensus models selected"}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                setResult(null);
                setCloneResult(null);
                setError(null);
              }}
              className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-line bg-white text-ink/70 hover:border-pine/50"
              title="Reset"
            >
              <RotateCcw aria-hidden className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={submit}
              disabled={loading}
              className="inline-flex h-9 items-center gap-2 rounded-md bg-pine px-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? <Loader2 aria-hidden className="h-4 w-4 animate-spin" /> : <Play aria-hidden className="h-4 w-4" />}
              Generate plan
            </button>
          </div>
        </div>

        <div className="scrollbar-thin p-4 sm:p-5 xl:h-[calc(100vh-3.5rem)] xl:overflow-auto">
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_18rem]">
            <section className="rounded-md border border-line bg-white p-4">
              <div className="grid gap-3 lg:grid-cols-2">
                <label className="block">
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <span className="block text-xs font-semibold uppercase text-ink/50">Issue URL</span>
                    <button
                      type="button"
                      onClick={loadIssueDetails}
                      disabled={issueLoading || !issueUrl.trim()}
                      className="inline-flex items-center gap-1 rounded-md border border-line bg-panel px-2 py-1 text-[11px] font-semibold uppercase text-ink/60 hover:border-pine/50 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {issueLoading ? <Loader2 aria-hidden className="h-3 w-3 animate-spin" /> : <Download aria-hidden className="h-3 w-3" />}
                      Fetch
                    </button>
                  </div>
                  <input
                    value={issueUrl}
                    onChange={(event) => setIssueUrl(event.target.value)}
                    className="h-10 w-full rounded-md border border-line bg-panel px-3 text-sm"
                  />
                </label>
                <label className="block">
                  <span className="mb-1 block text-xs font-semibold uppercase text-ink/50">Repository path</span>
                  <input
                    value={repositoryPath}
                    onChange={(event) => setRepositoryPath(event.target.value)}
                    placeholder="/workspace/project"
                    className="h-10 w-full rounded-md border border-line bg-panel px-3 text-sm"
                  />
                </label>
                <label className="block">
                  <span className="mb-1 block text-xs font-semibold uppercase text-ink/50">Clone URL</span>
                  <input
                    value={cloneUrl}
                    onChange={(event) => setCloneUrl(event.target.value)}
                    className="h-10 w-full rounded-md border border-line bg-panel px-3 text-sm"
                  />
                </label>
                <label className="block">
                  <span className="mb-1 block text-xs font-semibold uppercase text-ink/50">Clone target</span>
                  <input
                    value={cloneTarget}
                    onChange={(event) => setCloneTarget(event.target.value)}
                    placeholder="project"
                    className="h-10 w-full rounded-md border border-line bg-panel px-3 text-sm"
                  />
                </label>
              </div>
              <label className="mt-3 block">
                <span className="mb-1 block text-xs font-semibold uppercase text-ink/50">Issue summary</span>
                <textarea
                  value={issueSummary}
                  onChange={(event) => setIssueSummary(event.target.value)}
                  rows={4}
                  className="w-full resize-y rounded-md border border-line bg-panel px-3 py-2 text-sm leading-6"
                />
              </label>
              {issueDetails && (
                <div className="mt-3 rounded-md border border-line bg-panel p-3 text-xs text-ink/70">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] uppercase text-ink/50">
                    <span>{issueDetails.repository}</span>
                    <span>{issueDetails.state}</span>
                  </div>
                  <p className="mt-2 text-sm font-semibold text-ink">{issueDetails.title}</p>
                  <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-ink/60">
                    <span>#{issueDetails.number}</span>
                    <span>{issueDetails.comments} comments</span>
                    <span>by {issueDetails.author}</span>
                    {issueDetails.is_pull_request && <span>pull request</span>}
                  </div>
                  {issueDetails.labels.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {issueDetails.labels.map((label) => (
                        <span key={label} className="rounded-md border border-line bg-white px-2 py-0.5 text-[11px]">
                          {label}
                        </span>
                      ))}
                    </div>
                  )}
                  <a
                    href={issueDetails.html_url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-2 inline-flex text-[11px] font-semibold uppercase text-pine"
                  >
                    View on GitHub
                  </a>
                </div>
              )}
              {error && (
                <div className="mt-3 flex items-start gap-2 rounded-md border border-danger/30 bg-danger/10 p-3 text-sm text-danger">
                  <AlertCircle aria-hidden className="mt-0.5 h-4 w-4" />
                  <span className="min-w-0 break-words">{error}</span>
                </div>
              )}
            </section>

            <section className="space-y-3">
              <div className="grid grid-cols-2 rounded-md border border-line bg-white p-1">
                <button
                  type="button"
                  onClick={() => setMode("learn")}
                  className={`h-9 rounded-md text-sm ${mode === "learn" ? "bg-mint text-pine" : "text-ink/60"}`}
                >
                  Learn
                </button>
                <button
                  type="button"
                  onClick={() => setMode("auto_fix")}
                  className={`h-9 rounded-md text-sm ${mode === "auto_fix" ? "bg-mint text-pine" : "text-ink/60"}`}
                >
                  Auto fix
                </button>
              </div>
              <ApprovalGate
                status={result?.approval_status ?? "pending"}
                disabled={!result || loading}
                onDecision={decidePlan}
              />
              <div className="rounded-md border border-line bg-white p-3">
                <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
                  <GitBranchPlus aria-hidden className="h-4 w-4 text-pine" />
                  PR gate
                </div>
                <p className="text-sm leading-6 text-ink/65">Draft PR remains blocked until final review approval.</p>
              </div>
              <div className="rounded-md border border-line bg-white p-3">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div className="flex min-w-0 items-center gap-2 text-sm font-semibold">
                    <GitBranchPlus aria-hidden className="h-4 w-4 text-pine" />
                    <span className="truncate">Clone</span>
                  </div>
                  <span className="rounded-md bg-panel px-2 py-1 text-xs capitalize text-ink/70">
                    {cloneResult?.status ?? "pending"}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={cloneApprovedRepository}
                  disabled={!result || loading}
                  className="inline-flex h-9 w-full items-center justify-center gap-2 rounded-md border border-line bg-panel px-3 text-sm font-medium text-ink/75 hover:border-pine/50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {loading ? <Loader2 aria-hidden className="h-4 w-4 animate-spin" /> : <GitBranchPlus aria-hidden className="h-4 w-4" />}
                  Approved clone
                </button>
              </div>
            </section>
          </div>

          {cloneResult && (
            <section className="mt-5 rounded-md border border-line bg-white p-4">
              <div className="grid gap-4 md:grid-cols-3">
                <Metric label="Clone status" value={cloneResult.status} />
                <Metric label="Target" value={cloneResult.target_path} />
                <Metric label="Exit" value={String(cloneResult.exit_code ?? "pending")} />
              </div>
              {cloneResult.stderr && (
                <pre className="mt-3 max-h-40 overflow-auto rounded-md border border-line bg-panel p-3 text-xs leading-5 text-danger">
                  {cloneResult.stderr}
                </pre>
              )}
            </section>
          )}

          <section className="mt-5">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-sm font-semibold">Consensus models</h2>
              <span className="text-xs text-ink/50">{selections.length} selected</span>
            </div>
            <ProviderMatrix providers={providers} selections={selections} onChange={setSelections} />
          </section>

          {result?.repository && (
            <section className="mt-5 rounded-md border border-line bg-white p-4">
              <div className="grid gap-4 md:grid-cols-3">
                <Metric label="Languages" value={Object.keys(result.repository.languages).join(", ") || "Unknown"} />
                <Metric label="Frameworks" value={result.repository.frameworks.join(", ") || "None"} />
                <Metric label="Files" value={String(result.repository.code_quality_metrics.file_count ?? "0")} />
              </div>
            </section>
          )}
        </div>
      </section>

      <ReviewDashboard result={result} />
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <div className="text-xs font-semibold uppercase text-ink/50">{label}</div>
      <div className="mt-1 truncate text-sm font-medium">{value}</div>
    </div>
  );
}

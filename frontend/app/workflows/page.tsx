"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, ArrowLeft } from "lucide-react";
import { fetchWorkflows } from "@/lib/api";
import type { WorkflowListResult } from "@/lib/types";

export default function WorkflowsPage() {
  const router = useRouter();
  const [workflows, setWorkflows] = useState<WorkflowListResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [goodFirstIssue, setGoodFirstIssue] = useState(false);
  const [contributorLevel, setContributorLevel] = useState<string>("");
  const [minFixability, setMinFixability] = useState<number>(0);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchWorkflows({
          good_first_issue: goodFirstIssue || undefined,
          contributor_level: contributorLevel || undefined,
          min_fixability: minFixability > 0 ? minFixability : undefined,
        });
        setWorkflows(res.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load workflows");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [goodFirstIssue, contributorLevel, minFixability]);

  function handleRowClick(id: string) {
    if (typeof window !== "undefined") {
      localStorage.setItem("osca_workflow_id", id);
      router.push("/");
    }
  }

  return (
    <main className="min-h-screen bg-panel text-ink p-6 lg:p-10">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Workflows</h1>
            <p className="text-sm text-ink/60 mt-1">Browse and filter past repository agent workflows.</p>
          </div>
          <button
            onClick={() => router.push("/")}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md border border-line bg-white hover:bg-ink/5"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </button>
        </div>

        <div className="rounded-md border border-line bg-white p-4 flex flex-wrap gap-6 items-end shadow-sm">
          <label className="flex items-center gap-2 text-sm font-medium cursor-pointer">
            <input
              type="checkbox"
              checked={goodFirstIssue}
              onChange={(e) => setGoodFirstIssue(e.target.checked)}
              className="rounded border-line text-pine focus:ring-pine"
            />
            Good First Issue
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-ink/60 text-xs uppercase">Contributor Level</span>
            <select
              value={contributorLevel}
              onChange={(e) => setContributorLevel(e.target.value)}
              className="h-9 rounded-md border border-line bg-panel px-3 focus:border-pine focus:ring-1 focus:ring-pine"
            >
              <option value="">All levels</option>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </label>

          <label className="block text-sm min-w-[200px]">
            <span className="mb-1 flex justify-between font-medium text-ink/60 text-xs uppercase">
              <span>Min Fixability</span>
              <span>{minFixability}</span>
            </span>
            <input
              type="range"
              min="0"
              max="10"
              value={minFixability}
              onChange={(e) => setMinFixability(Number(e.target.value))}
              className="w-full accent-pine"
            />
          </label>
        </div>

        {error && <div className="text-rose-500 text-sm p-4 bg-rose-50 border border-rose-200 rounded-md">{error}</div>}

        <div className="rounded-md border border-line bg-white shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-panel border-b border-line text-xs uppercase text-ink/60">
                <tr>
                  <th className="px-4 py-3 font-semibold">Issue URL</th>
                  <th className="px-4 py-3 font-semibold">Repository</th>
                  <th className="px-4 py-3 font-semibold">Contributor Level</th>
                  <th className="px-4 py-3 font-semibold">Fixability</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold">Created Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-12 text-center">
                      <Loader2 className="h-6 w-6 animate-spin mx-auto text-ink/40" />
                    </td>
                  </tr>
                ) : workflows.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-12 text-center text-ink/50">
                      No workflows match your criteria.
                    </td>
                  </tr>
                ) : (
                  workflows.map((wf) => (
                    <tr
                      key={wf.id}
                      onClick={() => handleRowClick(wf.id)}
                      className="hover:bg-panel cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3 max-w-[200px] truncate text-pine font-medium" title={wf.issue_url}>
                        {wf.issue_url}
                      </td>
                      <td className="px-4 py-3 text-ink/80">
                        {wf.repository?.root ? wf.repository.root.split('/').pop() : "Not analyzed"}
                      </td>
                      <td className="px-4 py-3">
                        {wf.triage_data ? (
                          <span
                            className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                              wf.triage_data.contributor_level === "beginner"
                                ? "bg-emerald-100 text-emerald-700"
                                : wf.triage_data.contributor_level === "intermediate"
                                ? "bg-amber-100 text-amber-700"
                                : "bg-rose-100 text-rose-700"
                            }`}
                          >
                            {wf.triage_data.contributor_level}
                          </span>
                        ) : (
                          <span className="text-ink/40">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {wf.triage_data ? (
                          <div className="flex items-center gap-2">
                            <span>{wf.triage_data.fixability_score}</span>
                            <div className="h-1.5 w-16 overflow-hidden rounded-full bg-panel">
                              <div
                                className={`h-full ${wf.triage_data.fixability_score >= 7 ? "bg-emerald-500" : wf.triage_data.fixability_score >= 4 ? "bg-amber-500" : "bg-rose-500"} transition-all`}
                                style={{ width: `${(wf.triage_data.fixability_score / 10) * 100}%` }}
                              />
                            </div>
                          </div>
                        ) : (
                          <span className="text-ink/40">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-ink/10 text-ink/80">
                          {wf.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-ink/60 whitespace-nowrap">
                        {new Date(wf.created_at).toLocaleDateString(undefined, {
                          year: 'numeric', month: 'short', day: 'numeric'
                        })}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  );
}

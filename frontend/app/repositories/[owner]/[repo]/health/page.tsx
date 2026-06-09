'use client';
import { useEffect, useState } from 'react';

type RepoHealth = {
  open_issue_count: int;
  difficulty_breakdown: Record<string, number>;
  contributor_funnel: Record<string, number>;
  test_coverage_trend: number;
  stale_issue_count: number;
};

export default function RepoHealthDashboard({ params }: { params: { owner: string; repo: string } }) {
  const [health, setHealth] = useState<RepoHealth | null>(null);

  useEffect(() => {
    fetch(`http://localhost:8010/api/repositories/${params.owner}/${params.repo}/health`)
      .then(res => res.json())
      .then(setHealth);
  }, [params]);

  if (!health) return <div className="p-10 text-center">Loading health data...</div>;

  return (
    <div className="p-10 max-w-4xl mx-auto space-y-8">
      <h1 className="text-3xl font-bold text-gray-100">
        Repository Health: {params.owner}/{params.repo}
      </h1>

      <div className="grid grid-cols-3 gap-6">
        <div className="p-6 bg-gray-800 rounded-xl border border-gray-700">
          <div className="text-sm text-gray-400">Open Issues</div>
          <div className="text-4xl font-bold text-blue-400">{health.open_issue_count}</div>
        </div>
        <div className="p-6 bg-gray-800 rounded-xl border border-gray-700">
          <div className="text-sm text-gray-400">Stale Issues</div>
          <div className="text-4xl font-bold text-orange-400">{health.stale_issue_count}</div>
        </div>
        <div className="p-6 bg-gray-800 rounded-xl border border-gray-700">
          <div className="text-sm text-gray-400">Test Coverage</div>
          <div className="text-4xl font-bold text-green-400">{health.test_coverage_trend}%</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="p-6 bg-gray-800 rounded-xl border border-gray-700 space-y-4">
          <h2 className="text-xl font-semibold">Difficulty Breakdown</h2>
          <div className="space-y-2">
            {Object.entries(health.difficulty_breakdown).map(([level, count]) => (
              <div key={level} className="flex justify-between items-center">
                <span className="capitalize text-gray-300">{level}</span>
                <span className="font-mono text-gray-100 bg-gray-700 px-3 py-1 rounded-full">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="p-6 bg-gray-800 rounded-xl border border-gray-700 space-y-4">
          <h2 className="text-xl font-semibold">Contributor Funnel</h2>
          <div className="space-y-2">
            {Object.entries(health.contributor_funnel).map(([stage, count]) => (
              <div key={stage} className="flex justify-between items-center">
                <span className="capitalize text-gray-300">{stage}</span>
                <span className="font-mono text-gray-100 bg-gray-700 px-3 py-1 rounded-full">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

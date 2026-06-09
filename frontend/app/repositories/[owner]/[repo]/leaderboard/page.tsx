'use client';
import { useEffect, useState } from 'react';

type ContributorStats = {
  username: string;
  patches_merged: number;
  issues_resolved: number;
  review_score: number;
};

export default function LeaderboardPage({ params }: { params: { owner: string; repo: string } }) {
  const [leaderboard, setLeaderboard] = useState<ContributorStats[]>([]);

  useEffect(() => {
    fetch(`http://localhost:8010/api/repositories/${params.owner}/${params.repo}/leaderboard`)
      .then(res => res.json())
      .then(setLeaderboard);
  }, [params]);

  if (!leaderboard.length) return <div className="p-10 text-center">Loading leaderboard...</div>;

  return (
    <div className="p-10 max-w-4xl mx-auto space-y-8">
      <h1 className="text-3xl font-bold text-gray-100 flex items-center gap-3">
        🎖️ Contributor Leaderboard
        <span className="text-xl text-gray-400 font-normal">({params.owner}/{params.repo})</span>
      </h1>

      <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-900 border-b border-gray-700 text-gray-300">
            <tr>
              <th className="p-4 font-semibold">Rank</th>
              <th className="p-4 font-semibold">Username</th>
              <th className="p-4 font-semibold text-center">Patches Merged</th>
              <th className="p-4 font-semibold text-center">Issues Resolved</th>
              <th className="p-4 font-semibold text-center">Review Quality</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {leaderboard.map((contributor, idx) => (
              <tr key={contributor.username} className="hover:bg-gray-750 transition-colors">
                <td className="p-4 text-gray-400">#{idx + 1}</td>
                <td className="p-4 font-medium text-blue-400">@{contributor.username}</td>
                <td className="p-4 text-center font-mono">{contributor.patches_merged}</td>
                <td className="p-4 text-center font-mono">{contributor.issues_resolved}</td>
                <td className="p-4 text-center font-mono text-green-400">{contributor.review_score.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

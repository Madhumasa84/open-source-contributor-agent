"use client";

import { useState } from "react";
import { Search, ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import { semanticSearch } from "@/lib/api";
import type { SearchResult } from "@/lib/types";

export function SemanticSearchPanel({ workflowId }: { workflowId: string }) {
  const [expanded, setExpanded] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim() || !workflowId) return;

    setLoading(true);
    setError(null);
    try {
      const res = await semanticSearch(workflowId, query);
      setResults(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-md border border-line bg-white shadow-sm overflow-hidden">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between bg-panel px-4 py-3 text-sm font-semibold text-ink/80 hover:bg-ink/5"
      >
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4" />
          <span>Semantic Code Search</span>
        </div>
        {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>

      {expanded && (
        <div className="p-4 border-t border-line space-y-4">
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search concepts, e.g. 'authentication middleware'"
              className="h-9 flex-1 rounded-md border border-line bg-panel px-3 text-sm focus:border-pine focus:outline-none focus:ring-1 focus:ring-pine"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="inline-flex h-9 items-center justify-center rounded-md bg-pine px-4 text-sm font-medium text-white disabled:opacity-50"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
            </button>
          </form>

          {error && <div className="text-xs text-rose-500">{error}</div>}

          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="animate-pulse rounded-md border border-line p-3">
                  <div className="h-3 w-1/3 bg-line rounded mb-2"></div>
                  <div className="h-2 w-1/4 bg-line rounded mb-3"></div>
                  <div className="space-y-1">
                    <div className="h-2 w-full bg-line rounded"></div>
                    <div className="h-2 w-5/6 bg-line rounded"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : results.length > 0 ? (
            <div className="space-y-3 max-h-80 overflow-y-auto scrollbar-thin">
              {results.map((r, i) => (
                <div key={i} className="rounded-md border border-line bg-panel p-3 text-sm">
                  <div className="flex justify-between items-start mb-1">
                    <code className="text-xs font-mono text-pine bg-pine/10 px-1 py-0.5 rounded">
                      {r.file_path}
                    </code>
                    <span className="text-[10px] text-ink/50 font-medium bg-white px-1.5 py-0.5 rounded border border-line">
                      Score: {r.score.toFixed(2)}
                    </span>
                  </div>
                  <div className="text-xs text-ink/60 mb-2">
                    Lines {r.start_line} - {r.end_line}
                  </div>
                  <pre className="text-xs font-mono text-ink/80 bg-white p-2 rounded border border-line overflow-x-auto">
                    {r.content.split("\n").slice(0, 3).join("\n")}
                    {r.content.split("\n").length > 3 && "\n..."}
                  </pre>
                </div>
              ))}
            </div>
          ) : (
            query && !loading && (
              <div className="text-sm text-ink/50 text-center py-4">No results found.</div>
            )
          )}
        </div>
      )}
    </div>
  );
}

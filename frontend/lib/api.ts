import type {
  ApprovalResponse,
  ApprovalStatus,
  CloneRepositoryResponse,
  GitHubIssueDetails,
  ProviderDescriptor,
  ProviderSelection,
  WorkflowPlanResponse,
  SearchResult,
  WorkflowListResult
} from "./types";

export interface GitHubIssueTriageResponse {
  issue: GitHubIssueDetails;
  triage: any;
  workflow_id: string;
  detected_language: string | null;
  translation_warning: string | null;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function fetchProviders(): Promise<ProviderDescriptor[]> {
  const response = await fetch(`${API_BASE_URL}/api/providers`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Provider request failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchGitHubIssue(issueUrl: string, preferredLanguage: string = "en"): Promise<GitHubIssueTriageResponse> {
  const response = await fetch(`${API_BASE_URL}/api/github/issue`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ issue_url: issueUrl, preferred_language: preferredLanguage })
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Issue request failed: ${response.status}`);
  }
  return response.json();
}

export async function createWorkflowPlan(input: {
  issueUrl: string;
  repositoryPath?: string;
  issueSummary?: string;
  mode: "learn" | "auto_fix";
  providers: ProviderSelection[];
  preferredLanguage: string;
}): Promise<WorkflowPlanResponse> {
  const response = await fetch(`${API_BASE_URL}/api/workflows/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      issue_url: input.issueUrl,
      repository_path: input.repositoryPath || null,
      issue_summary: input.issueSummary || null,
      mode: input.mode,
      providers: input.providers,
      preferred_language: input.preferredLanguage
    })
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Workflow request failed: ${response.status}`);
  }
  return response.json();
}

export async function submitApproval(input: {
  workflowId: string;
  gate: "plan" | "final";
  actor: string;
  decision: ApprovalStatus;
  notes?: string;
}): Promise<ApprovalResponse> {
  const response = await fetch(`${API_BASE_URL}/api/workflows/${input.workflowId}/approvals/${input.gate}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      actor: input.actor,
      decision: input.decision,
      notes: input.notes ?? null
    })
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Approval request failed: ${response.status}`);
  }
  return response.json();
}

export async function cloneRepository(input: {
  workflowId: string;
  repositoryUrl: string;
  approvedBy: string;
  targetName?: string;
}): Promise<CloneRepositoryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/workflows/${input.workflowId}/repository/clone`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      repository_url: input.repositoryUrl,
      approved_by: input.approvedBy,
      target_name: input.targetName || null
    })
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Clone request failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchWorkflow(workflowId: string): Promise<WorkflowPlanResponse> {
  const response = await fetch(`${API_BASE_URL}/api/workflows/${workflowId}`, { cache: "no-store" });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Workflow fetch failed: ${response.status}`);
  }
  return response.json();
}

export async function runTests(workflowId: string): Promise<WorkflowPlanResponse> {
  const response = await fetch(`${API_BASE_URL}/api/workflows/${workflowId}/run-tests`, {
    method: "POST"
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Tests run failed: ${response.status}`);
  }
  return response.json();
}

export async function runSecurityScan(workflowId: string): Promise<WorkflowPlanResponse> {
  const response = await fetch(`${API_BASE_URL}/api/workflows/${workflowId}/security-scan`, {
    method: "POST"
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Security scan failed: ${response.status}`);
  }
  return response.json();
}

export async function semanticSearch(workflowId: string, query: string): Promise<SearchResult[]> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      workflow_id: workflowId,
      query,
      top_k: 10
    })
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Search request failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchWorkflows(params?: { good_first_issue?: boolean; contributor_level?: string; min_fixability?: number }): Promise<{ data: WorkflowListResult[]; total: number }> {
  const query = new URLSearchParams();
  if (params?.good_first_issue) query.append("good_first_issue", "true");
  if (params?.contributor_level) query.append("contributor_level", params.contributor_level);
  if (params?.min_fixability) query.append("min_fixability", params.min_fixability.toString());

  const response = await fetch(`${API_BASE_URL}/api/workflows?${query.toString()}`, { cache: "no-store" });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Workflows fetch failed: ${response.status}`);
  }
  return response.json();
}

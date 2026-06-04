export type ApprovalStatus = "pending" | "approved" | "rejected" | "changes_requested";
export type WorkflowStage =
  | "created"
  | "repository_analyzed"
  | "plan_generated"
  | "plan_approved"
  | "changes_generated"
  | "tests_completed"
  | "security_completed"
  | "review_ready"
  | "final_approved"
  | "draft_pr_ready";

export type ProviderDescriptor = {
  name: "gemini" | "anthropic" | "openrouter" | "ollama";
  configured: boolean;
  default_models: string[];
  capabilities: {
    streaming: boolean;
    tool_calling: boolean;
    local: boolean;
  };
};

export type ProviderSelection = {
  provider: ProviderDescriptor["name"];
  model: string;
  role: string;
};

export type GitHubIssueDetails = {
  repository: string;
  number: number;
  title: string;
  body: string;
  state: string;
  labels: string[];
  author: string;
  comments: number;
  created_at: string | null;
  updated_at: string | null;
  url: string;
  html_url: string;
  is_pull_request: boolean;
};

export type RepositoryOverview = {
  root: string;
  languages: Record<string, number>;
  frameworks: string[];
  dependencies: Record<string, string[]>;
  test_frameworks: string[];
  build_systems: string[];
  architecture: string[];
  important_files: string[];
  entry_points: string[];
  risks: string[];
  code_quality_metrics: Record<string, string | number>;
  contribution_difficulty: "Easy" | "Medium" | "Hard" | "Expert";
};

export type WorkflowPlanResponse = {
  workflow_id: string;
  issue_url: string;
  mode: "learn" | "auto_fix";
  repository_path: string | null;
  stage: WorkflowStage;
  approval_status: ApprovalStatus;
  final_approval_status: ApprovalStatus;
  repository: RepositoryOverview | null;
  difficulty: {
    level: "Easy" | "Medium" | "Hard" | "Expert";
    files_impacted: number;
    estimated_work: string;
    confidence: number;
    rationale: string[];
  };
  mentor: {
    what_is_broken: string;
    why_it_is_broken: string;
    relevant_files: string[];
    relevant_functions: string[];
    possible_solutions: string[];
  };
  plan: {
    summary: string;
    root_cause: string;
    proposed_steps: string[];
    files_to_inspect: string[];
    files_likely_changed: string[];
    tests_to_run: string[];
    risks: string[];
    approval_required: boolean;
  };
  consensus: {
    score: number;
    agreement: string[];
    disagreement: string[];
    model_notes: Record<string, string>;
  } | null;
  review_report: ReviewReport | null;
  audit_events: Array<Record<string, unknown>>;
};

export type ReviewReport = {
  issue_summary: string;
  root_cause: string;
  files_changed: string[];
  code_diff: string | null;
  tests_run: string[];
  coverage: string | null;
  security_review: {
    score: number;
    findings: Array<{
      rule: string;
      file: string;
      line: number;
      severity: "Low" | "Medium" | "High" | "Critical";
      message: string;
    }>;
    summary: string;
  } | null;
  impact_analysis: {
    files_modified: string[];
    functions_modified: string[];
    classes_modified: string[];
    dependency_impact: string[];
    risk_level: "Low" | "Medium" | "High" | "Critical";
  } | null;
  risk_assessment: string[];
  reasoning: string[];
};

export type ApprovalResponse = {
  workflow_id: string;
  gate: string;
  status: ApprovalStatus;
  next_stage: WorkflowStage;
};

export type CloneRepositoryResponse = {
  job_id: string;
  workflow_id: string;
  repository_url: string;
  target_path: string;
  status: "completed" | "failed" | "pending";
  approved_by: string;
  exit_code: number | null;
  stdout: string;
  stderr: string;
};

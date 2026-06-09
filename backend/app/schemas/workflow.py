from enum import StrEnum
from typing import Any, Literal

from pydantic import AnyUrl, BaseModel, Field

from app.schemas.provider import ProviderSelection
from app.schemas.repository import (
    DifficultyEstimate,
    RepositoryOverview,
    SecurityReview,
    ImpactAnalysis,
)


class ApprovalStatus(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    changes_requested = "changes_requested"


class WorkflowStage(StrEnum):
    created = "created"
    triaged = "triaged"
    repository_analyzed = "repository_analyzed"
    plan_generated = "plan_generated"
    plan_approved = "plan_approved"
    changes_generated = "changes_generated"
    tests_completed = "tests_completed"
    security_completed = "security_completed"
    review_ready = "review_ready"
    final_approved = "final_approved"
    draft_pr_ready = "draft_pr_ready"


class IssuePlanRequest(BaseModel):
    issue_url: AnyUrl
    repository_path: str | None = None
    issue_summary: str | None = None
    mode: Literal["learn", "auto_fix"] = "learn"
    providers: list[ProviderSelection] = Field(default_factory=list)
    preferred_language: str = "en"


class MentorExplanation(BaseModel):
    what_is_broken: str
    why_it_is_broken: str
    relevant_files: list[str]
    relevant_functions: list[str]
    possible_solutions: list[str]


class FixPlan(BaseModel):
    summary: str
    root_cause: str
    proposed_steps: list[str]
    files_to_inspect: list[str]
    files_likely_changed: list[str]
    tests_to_run: list[str]
    risks: list[str]
    approval_required: bool = True


class ConsensusReview(BaseModel):
    score: float = Field(ge=0, le=1)
    agreement: list[str]
    disagreement: list[str]
    model_notes: dict[str, str]


class ReviewReport(BaseModel):
    issue_summary: str
    root_cause: str
    files_changed: list[str]
    code_diff: str | None = None
    tests_run: list[str]
    coverage: str | None = None
    security_review: SecurityReview | None = None
    impact_analysis: ImpactAnalysis | None = None
    risk_assessment: list[str]
    reasoning: list[str]


class WorkflowPlanResponse(BaseModel):
    workflow_id: str
    issue_url: str
    mode: str
    repository_path: str | None = None
    stage: WorkflowStage
    approval_status: ApprovalStatus
    final_approval_status: ApprovalStatus = ApprovalStatus.pending
    repository: RepositoryOverview | None
    difficulty: DifficultyEstimate
    mentor: MentorExplanation
    plan: FixPlan
    consensus: ConsensusReview | None = None
    review_report: ReviewReport | None = None
    audit_events: list[dict[str, Any]]
    translation_warning: str | None = None
    triage_data: dict[str, Any] | None = None
    patch_diff: str | None = None
    patch_iterations: int | None = None
    patch_test_status: str | None = None


class ApprovalRequest(BaseModel):
    actor: str
    decision: ApprovalStatus
    notes: str | None = None


class ApprovalResponse(BaseModel):
    workflow_id: str
    gate: str
    status: ApprovalStatus
    next_stage: WorkflowStage


class CloneRepositoryRequest(BaseModel):
    repository_url: AnyUrl
    approved_by: str = Field(min_length=1)
    target_name: str | None = None
    depth: int = Field(default=1, ge=1, le=1000)


class CloneRepositoryResponse(BaseModel):
    job_id: str
    workflow_id: str
    repository_url: str
    target_path: str
    status: str
    approved_by: str
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""

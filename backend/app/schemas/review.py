from pydantic import BaseModel, Field

from app.schemas.repository import ImpactAnalysis, SecurityReview
from app.schemas.workflow import FixPlan


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


class PRDraft(BaseModel):
    title: str
    body: str
    labels: list[str] = Field(default_factory=list)
    ready_to_publish: bool = False
    blocked_reason: str | None = "Requires final human approval before GitHub PR creation."


class PRDraftRequest(BaseModel):
    issue_url: str
    plan: FixPlan
    review_report: ReviewReport | None = None

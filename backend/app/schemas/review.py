from pydantic import BaseModel, Field

from app.schemas.workflow import FixPlan, ReviewReport


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

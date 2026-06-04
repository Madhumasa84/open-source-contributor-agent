from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.ai.providers.registry import ProviderRegistry
from app.schemas.repository import DifficultyEstimate, RepositoryOverview
from app.schemas.workflow import (
    ApprovalStatus,
    ConsensusReview,
    FixPlan,
    IssuePlanRequest,
    MentorExplanation,
    WorkflowPlanResponse,
    WorkflowStage,
)
from app.schemas.review import ReviewReport
from app.services.audit import AuditLogger, AuditRecord
from app.services.difficulty import DifficultyEstimator
from app.services.repository_analyzer import RepositoryAnalyzer


class ApprovalRequiredError(RuntimeError):
    pass


@dataclass
class WorkflowState:
    workflow_id: str
    issue_url: str
    mode: str
    repository_path: str | None = None
    stage: WorkflowStage = WorkflowStage.created
    plan_approval: ApprovalStatus = ApprovalStatus.pending
    final_approval: ApprovalStatus = ApprovalStatus.pending
    repository: RepositoryOverview | None = None
    difficulty: DifficultyEstimate | None = None
    mentor: MentorExplanation | None = None
    plan: FixPlan | None = None
    consensus: ConsensusReview | None = None
    review_report: ReviewReport | None = None
    audit: AuditLogger = field(default_factory=AuditLogger)


class OpenSourceContributorWorkflow:
    def __init__(
        self,
        analyzer: RepositoryAnalyzer | None = None,
        estimator: DifficultyEstimator | None = None,
        provider_registry: ProviderRegistry | None = None,
    ) -> None:
        self.analyzer = analyzer or RepositoryAnalyzer()
        self.estimator = estimator or DifficultyEstimator()
        self.provider_registry = provider_registry or ProviderRegistry()

    async def generate_plan(self, request: IssuePlanRequest) -> WorkflowPlanResponse:
        state = WorkflowState(
            workflow_id=str(uuid4()),
            issue_url=str(request.issue_url),
            repository_path=request.repository_path,
            mode=request.mode,
        )
        await state.audit.record(
            AuditRecord(
                action="workflow.created",
                input_summary=str(request.issue_url),
                metadata={
                    "mode": request.mode,
                    "providers": [provider.model_dump() for provider in request.providers],
                },
            )
        )

        if request.repository_path:
            state.repository = await self.analyzer.analyze(request.repository_path)
            state.stage = WorkflowStage.repository_analyzed
            await state.audit.record(
                AuditRecord(
                    action="repository.analyzed",
                    output_summary=f"{state.repository.code_quality_metrics['file_count']} files",
                    metadata={
                        "languages": state.repository.languages,
                        "frameworks": state.repository.frameworks,
                    },
                )
            )

        state.difficulty = self.estimator.estimate(request.issue_summary, state.repository)
        state.mentor = self._mentor_explanation(request, state.repository)
        state.plan = self._deterministic_plan(request, state.repository, state.difficulty)
        state.consensus = self._consensus_stub(request)
        state.stage = WorkflowStage.plan_generated
        await state.audit.record(
            AuditRecord(
                action="workflow.plan_generated",
                status="awaiting_human_approval",
                output_summary=state.plan.summary,
                metadata={"difficulty": state.difficulty.level.value, "approval_gate": "plan"},
            )
        )
        return self._response(state)

    async def approve_plan(
        self, state: WorkflowState, actor: str, decision: ApprovalStatus
    ) -> WorkflowState:
        state.plan_approval = decision
        if decision == ApprovalStatus.approved:
            state.stage = WorkflowStage.plan_approved
        await state.audit.record(
            AuditRecord(
                action="approval.plan",
                actor=actor,
                status=decision.value,
                approval_id=actor,
                metadata={"workflow_id": state.workflow_id},
            )
        )
        return state

    async def assert_final_approval(self, state: WorkflowState) -> None:
        if state.final_approval != ApprovalStatus.approved:
            await state.audit.record(
                AuditRecord(
                    action="approval.final.blocked",
                    status="blocked",
                    metadata={"workflow_id": state.workflow_id, "required_gate": "final_review"},
                )
            )
            raise ApprovalRequiredError("draft PR creation requires final human approval")

    def _mentor_explanation(
        self,
        request: IssuePlanRequest,
        repository: RepositoryOverview | None,
    ) -> MentorExplanation:
        relevant_files = repository.important_files[:8] if repository else []
        return MentorExplanation(
            what_is_broken=request.issue_summary
            or "The issue needs repository analysis before a specific fault is known.",
            why_it_is_broken=(
                "The agent has not modified code yet. It first builds a traceable "
                "hypothesis and waits for approval."
            ),
            relevant_files=relevant_files,
            relevant_functions=[],
            possible_solutions=[
                "Reproduce the issue with the smallest test or command available.",
                "Inspect the entry points and nearby tests identified by the repository analyzer.",
                "Make the narrowest change that resolves the root cause, then run "
                "tests and security checks.",
            ],
        )

    def _deterministic_plan(
        self,
        request: IssuePlanRequest,
        repository: RepositoryOverview | None,
        difficulty: DifficultyEstimate,
    ) -> FixPlan:
        files_to_inspect = repository.entry_points[:6] if repository else []
        if repository:
            files_to_inspect.extend(repository.important_files[:6])
        files_to_inspect = sorted(set(files_to_inspect))
        tests = (
            repository.test_frameworks
            if repository and repository.test_frameworks
            else ["targeted regression test"]
        )
        plan_summary = (
            f"Investigate {request.issue_url} and prepare a "
            f"{difficulty.level.value.lower()} scoped fix."
        )
        return FixPlan(
            summary=plan_summary,
            root_cause="Unknown until reproduction and code inspection complete.",
            proposed_steps=[
                "Clone or open the target repository in an isolated workspace.",
                "Analyze languages, dependency metadata, tests, and entry points.",
                "Reproduce the issue or create a failing characterization test.",
                "Generate the smallest code change that fixes the root cause.",
                "Run tests, linting, type checks, and security review.",
                "Present the review dashboard for final human approval before any PR action.",
            ],
            files_to_inspect=files_to_inspect,
            files_likely_changed=files_to_inspect[:4],
            tests_to_run=tests,
            risks=repository.risks
            if repository
            else ["Repository has not been analyzed locally yet."],
        )

    def _consensus_stub(self, request: IssuePlanRequest) -> ConsensusReview | None:
        if not request.providers:
            return None
        notes = {
            f"{selection.provider.value}:{selection.model}": f"Assigned role: {selection.role}"
            for selection in request.providers
        }
        return ConsensusReview(
            score=0.5,
            agreement=["All selected models will review the plan before code generation."],
            disagreement=["No model calls have been executed in this deterministic planning pass."],
            model_notes=notes,
        )

    def _response(self, state: WorkflowState) -> WorkflowPlanResponse:
        if not state.difficulty or not state.mentor or not state.plan:
            raise RuntimeError("workflow state is incomplete")
        return WorkflowPlanResponse(
            workflow_id=state.workflow_id,
            issue_url=state.issue_url,
            mode=state.mode,
            repository_path=state.repository_path,
            stage=state.stage,
            approval_status=state.plan_approval,
            final_approval_status=state.final_approval,
            repository=state.repository,
            difficulty=state.difficulty,
            mentor=state.mentor,
            plan=state.plan,
            consensus=state.consensus,
            review_report=state.review_report,
            audit_events=state.audit.public_events(),
        )

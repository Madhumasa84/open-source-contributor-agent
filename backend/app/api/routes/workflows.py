from fastapi import APIRouter, HTTPException

from app.agents.workflow import OpenSourceContributorWorkflow, WorkflowState
from app.schemas.review import PRDraft, PRDraftRequest
from app.schemas.workflow import (
    ApprovalRequest,
    ApprovalResponse,
    ApprovalStatus,
    CloneRepositoryRequest,
    CloneRepositoryResponse,
    IssuePlanRequest,
    WorkflowPlanResponse,
    WorkflowStage,
    ReviewReport,
)
from app.services.pr_draft import PRDraftGenerator
from app.services.repository_clone import RepositoryCloneError, RepositoryCloneService
from app.services.workflow_persistence import WorkflowPersistenceService
from app.services.test_runner import TestExecutionEngine
from app.services.security import SecurityReviewer
from app.tools.safe_executor import SafeToolExecutor
from app.services.audit import AuditLogger, AuditRecord

router = APIRouter(prefix="/workflows", tags=["workflows"])
workflow_engine = OpenSourceContributorWorkflow()
workflow_store: dict[str, WorkflowState] = {}
persistence = WorkflowPersistenceService()


@router.post("/plan", response_model=WorkflowPlanResponse)
async def generate_plan(request: IssuePlanRequest) -> WorkflowPlanResponse:
    response = await workflow_engine.generate_plan(request)
    workflow_store[response.workflow_id] = WorkflowState(
        workflow_id=response.workflow_id,
        issue_url=str(request.issue_url),
        repository_path=request.repository_path,
        mode=request.mode,
        stage=response.stage,
        plan_approval=response.approval_status,
        repository=response.repository,
        difficulty=response.difficulty,
        mentor=response.mentor,
        plan=response.plan,
        consensus=response.consensus,
    )
    await persistence.save_plan(request, response)
    return response


async def get_or_load_workflow(workflow_id: str) -> WorkflowState:
    state = workflow_store.get(workflow_id)
    if not state:
        state = await persistence.get_workflow(workflow_id)
        if state:
            workflow_store[workflow_id] = state
    if not state:
        raise HTTPException(status_code=404, detail="workflow not found")
    return state


@router.get("/{workflow_id}", response_model=WorkflowPlanResponse)
async def get_workflow(workflow_id: str) -> WorkflowPlanResponse:
    state = await get_or_load_workflow(workflow_id)
    return workflow_engine._response(state)


@router.post("/{workflow_id}/approvals/plan", response_model=ApprovalResponse)
async def approve_plan(workflow_id: str, request: ApprovalRequest) -> ApprovalResponse:
    state = await get_or_load_workflow(workflow_id)
    state.plan_approval = request.decision
    state.stage = (
        WorkflowStage.plan_approved if request.decision == ApprovalStatus.approved else state.stage
    )
    await persistence.update_plan_approval(workflow_id, state.plan_approval, state.stage.value)
    return ApprovalResponse(
        workflow_id=workflow_id,
        gate="plan",
        status=state.plan_approval,
        next_stage=state.stage,
    )


@router.post("/{workflow_id}/approvals/final", response_model=ApprovalResponse)
async def approve_final(workflow_id: str, request: ApprovalRequest) -> ApprovalResponse:
    state = await get_or_load_workflow(workflow_id)
    state.final_approval = request.decision
    state.stage = (
        WorkflowStage.final_approved if request.decision == ApprovalStatus.approved else state.stage
    )
    await persistence.update_final_approval(workflow_id, state.final_approval, state.stage.value)
    return ApprovalResponse(
        workflow_id=workflow_id,
        gate="final_review",
        status=state.final_approval,
        next_stage=state.stage,
    )


@router.post("/{workflow_id}/pr-draft", response_model=PRDraft)
async def generate_pr_draft(workflow_id: str, request: PRDraftRequest) -> PRDraft:
    state = await get_or_load_workflow(workflow_id)
    return PRDraftGenerator().generate(
        issue_url=request.issue_url,
        plan=request.plan,
        review_report=request.review_report,
        final_approved=state.final_approval == ApprovalStatus.approved,
    )


@router.post("/{workflow_id}/github/draft-pr")
async def create_github_draft_pr(workflow_id: str) -> dict[str, str]:
    state = await get_or_load_workflow(workflow_id)
    try:
        await workflow_engine.assert_final_approval(state)
    except RuntimeError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {
        "status": "ready",
        "message": (
            "Final approval is present. GitHub publishing adapter can run in the next phase."
        ),
    }


@router.post("/{workflow_id}/repository/clone", response_model=CloneRepositoryResponse)
async def clone_repository(
    workflow_id: str,
    request: CloneRepositoryRequest,
) -> CloneRepositoryResponse:
    state = await get_or_load_workflow(workflow_id)
    try:
        response = await RepositoryCloneService().clone(workflow_id, request)
    except RepositoryCloneError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if response.status == "completed":
        state.repository_path = response.target_path
        await persistence.update_repository_path(workflow_id, response.target_path)
    return response


@router.post("/{workflow_id}/run-tests", response_model=WorkflowPlanResponse)
async def run_tests(workflow_id: str) -> WorkflowPlanResponse:
    state = await get_or_load_workflow(workflow_id)
    if not state.repository_path:
        raise HTTPException(
            status_code=400, detail="Repository path is not set. Clone repository first."
        )

    executor = SafeToolExecutor(state.audit)
    runner = TestExecutionEngine(executor)
    results = await runner.run(state.repository_path, approved_by="human")
    all_success = all(r.exit_code == 0 for r in results)

    if not state.review_report:
        state.review_report = ReviewReport(
            issue_summary=state.plan.summary,
            root_cause=state.plan.root_cause,
            files_changed=state.plan.files_likely_changed,
            tests_run=[f" ".join(r.command) for r in results],
            risk_assessment=state.plan.risks,
            reasoning=["Tests executed by human operator request."],
        )
    else:
        state.review_report.tests_run = [f" ".join(r.command) for r in results]

    state.stage = WorkflowStage.tests_completed

    await state.audit.record(
        AuditRecord(
            action="tests.run",
            actor="human",
            status="completed" if all_success else "failed",
            input_summary=",".join([f" ".join(r.command) for r in results]),
            output_summary=f"Success: {all_success}",
            metadata={"workflow_id": workflow_id},
        )
    )

    await persistence.update_review_report(workflow_id, state.review_report, state.stage.value)
    return workflow_engine._response(state)


@router.post("/{workflow_id}/security-scan", response_model=WorkflowPlanResponse)
async def run_security_scan(workflow_id: str) -> WorkflowPlanResponse:
    state = await get_or_load_workflow(workflow_id)
    if not state.repository_path:
        raise HTTPException(
            status_code=400, detail="Repository path is not set. Clone repository first."
        )

    files_to_check = state.plan.files_to_inspect + state.plan.files_likely_changed
    files_to_check = sorted(list(set(files_to_check)))

    reviewer = SecurityReviewer()
    report = reviewer.review_files(state.repository_path, files_to_check)

    if not state.review_report:
        state.review_report = ReviewReport(
            issue_summary=state.plan.summary,
            root_cause=state.plan.root_cause,
            files_changed=state.plan.files_likely_changed,
            tests_run=[],
            security_review=report,
            risk_assessment=state.plan.risks,
            reasoning=["Security review performed by human operator request."],
        )
    else:
        state.review_report.security_review = report

    state.stage = WorkflowStage.security_completed

    await state.audit.record(
        AuditRecord(
            action="security.scan",
            actor="human",
            status="completed",
            input_summary=f"{len(files_to_check)} files",
            output_summary=f"Score: {report.score}, findings: {len(report.findings)}",
            metadata={"workflow_id": workflow_id},
        )
    )

    await persistence.update_review_report(workflow_id, state.review_report, state.stage.value)
    return workflow_engine._response(state)

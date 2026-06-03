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
)
from app.services.pr_draft import PRDraftGenerator
from app.services.repository_clone import RepositoryCloneError, RepositoryCloneService
from app.services.workflow_persistence import WorkflowPersistenceService

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


@router.post("/{workflow_id}/approvals/plan", response_model=ApprovalResponse)
async def approve_plan(workflow_id: str, request: ApprovalRequest) -> ApprovalResponse:
    state = workflow_store.get(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="workflow not found")
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
    state = workflow_store.get(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="workflow not found")
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
    state = workflow_store.get(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="workflow not found")
    return PRDraftGenerator().generate(
        issue_url=request.issue_url,
        plan=request.plan,
        review_report=request.review_report,
        final_approved=state.final_approval == ApprovalStatus.approved,
    )


@router.post("/{workflow_id}/github/draft-pr")
async def create_github_draft_pr(workflow_id: str) -> dict[str, str]:
    state = workflow_store.get(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="workflow not found")
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
    state = workflow_store.get(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="workflow not found")
    try:
        response = await RepositoryCloneService().clone(workflow_id, request)
    except RepositoryCloneError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if response.status == "completed":
        state.repository_path = response.target_path
    return response

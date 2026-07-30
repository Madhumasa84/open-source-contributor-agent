import pytest
from fastapi.testclient import TestClient

from app.agents.workflow import ApprovalRequiredError, OpenSourceContributorWorkflow, WorkflowState
from app.api.routes.workflows import workflow_store
from app.main import app
from app.schemas.workflow import ApprovalStatus
from app.services.audit import AuditLogger, MemoryAuditSink


@pytest.mark.asyncio
async def test_final_pr_gate_blocks_without_human_approval():
    workflow = OpenSourceContributorWorkflow()
    state = WorkflowState(
        workflow_id="wf-1",
        issue_url="https://github.com/example/project/issues/1",
        mode="learn",
        audit=AuditLogger(sink=MemoryAuditSink()),
    )

    with pytest.raises(ApprovalRequiredError):
        await workflow.assert_final_approval(state)

    assert state.audit.public_events()[0]["action"] == "approval.final.blocked"


def test_api_patch_gate_blocks_without_plan_approval():
    client = TestClient(app)
    workflow_id = "test-wf-patch"
    audit_logger = AuditLogger(sink=MemoryAuditSink())
    workflow_store[workflow_id] = WorkflowState(
        workflow_id=workflow_id,
        issue_url="https://github.com/example/project/issues/2",
        mode="fix",
        audit=audit_logger,
        plan_approval=ApprovalStatus.pending,
    )

    response = client.post(f"/api/workflows/{workflow_id}/patch")

    assert response.status_code == 403
    assert response.json()["detail"] == "Gate 1 (Plan) approval is required."

    events = audit_logger.public_events()
    assert len(events) == 1
    assert events[0]["action"] == "approval.plan.blocked"


def test_api_pr_draft_gate_blocks_without_final_approval():
    client = TestClient(app)
    workflow_id = "test-wf-pr-draft"
    audit_logger = AuditLogger(sink=MemoryAuditSink())
    workflow_store[workflow_id] = WorkflowState(
        workflow_id=workflow_id,
        issue_url="https://github.com/example/project/issues/2",
        mode="fix",
        audit=audit_logger,
        plan_approval=ApprovalStatus.approved,
        final_approval=ApprovalStatus.pending,
    )

    # Check /pr-draft endpoint
    payload = {
        "issue_url": "https://github.com/example/project/issues/2",
        "plan": {"summary": "", "root_cause": "", "proposed_steps": [], "files_to_inspect": [], "files_likely_changed": [], "tests_to_run": [], "risks": []},
        "review_report": {"issue_summary": "", "root_cause": "", "files_changed": [], "tests_run": [], "risk_assessment": [], "reasoning": []}
    }
    response = client.post(f"/api/workflows/{workflow_id}/pr-draft", json=payload)

    assert response.status_code == 403
    assert response.json()["detail"] == "Gate 2 (Final) approval is required."

    events = audit_logger.public_events()
    assert len(events) == 1
    assert events[0]["action"] == "approval.final.blocked"

    # Check /github/draft-pr endpoint
    response = client.post(f"/api/workflows/{workflow_id}/github/draft-pr")

    assert response.status_code == 403
    assert response.json()["detail"] == "Gate 2 (Final) approval is required."

    events = audit_logger.public_events()
    assert len(events) == 2
    assert events[1]["action"] == "approval.final.blocked"

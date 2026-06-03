import pytest

from app.agents.workflow import ApprovalRequiredError, OpenSourceContributorWorkflow, WorkflowState


@pytest.mark.asyncio
async def test_final_pr_gate_blocks_without_human_approval():
    workflow = OpenSourceContributorWorkflow()
    state = WorkflowState(
        workflow_id="wf-1",
        issue_url="https://github.com/example/project/issues/1",
        mode="learn",
    )

    with pytest.raises(ApprovalRequiredError):
        await workflow.assert_final_approval(state)

    assert state.audit.public_events()[0]["action"] == "approval.final.blocked"

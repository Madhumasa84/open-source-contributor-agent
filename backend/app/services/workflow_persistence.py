from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.workflow import WorkflowRun
from app.schemas.workflow import ApprovalStatus, IssuePlanRequest, WorkflowPlanResponse


class WorkflowPersistenceService:
    async def save_plan(self, request: IssuePlanRequest, response: WorkflowPlanResponse) -> bool:
        return await self._with_session(self._save_plan, request, response)

    async def update_plan_approval(
        self,
        workflow_id: str,
        status: ApprovalStatus,
        stage: str,
    ) -> bool:
        return await self._with_session(
            self._update_approval,
            workflow_id,
            "plan_approval_status",
            status.value,
            stage,
        )

    async def update_final_approval(
        self,
        workflow_id: str,
        status: ApprovalStatus,
        stage: str,
    ) -> bool:
        return await self._with_session(
            self._update_approval,
            workflow_id,
            "final_approval_status",
            status.value,
            stage,
        )

    async def _with_session(self, operation, *args) -> bool:
        try:
            async with AsyncSessionLocal() as session:
                await operation(session, *args)
                await session.commit()
            return True
        except SQLAlchemyError:
            return False
        except OSError:
            return False

    async def _save_plan(
        self,
        session: AsyncSession,
        request: IssuePlanRequest,
        response: WorkflowPlanResponse,
    ) -> None:
        workflow = WorkflowRun(
            id=response.workflow_id,
            issue_url=str(request.issue_url),
            repository_path=request.repository_path,
            mode=request.mode,
            stage=response.stage.value,
            status="awaiting_plan_approval",
            plan_approval_status=response.approval_status.value,
            final_approval_status="pending",
            repository=response.repository.model_dump(mode="json") if response.repository else {},
            difficulty=response.difficulty.model_dump(mode="json"),
            mentor=response.mentor.model_dump(mode="json"),
            plan=response.plan.model_dump(mode="json"),
            consensus=response.consensus.model_dump(mode="json") if response.consensus else {},
            audit_events=response.audit_events,
        )
        session.add(workflow)

    async def _update_approval(
        self,
        session: AsyncSession,
        workflow_id: str,
        column_name: str,
        status: str,
        stage: str,
    ) -> None:
        workflow = await session.get(WorkflowRun, workflow_id)
        if not workflow:
            return
        setattr(workflow, column_name, status)
        workflow.stage = stage
        workflow.status = f"{column_name}:{status}"

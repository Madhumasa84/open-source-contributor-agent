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

    async def update_repository_path(
        self,
        workflow_id: str,
        repository_path: str,
    ) -> bool:
        return await self._with_session(
            self._update_repository_path,
            workflow_id,
            repository_path,
        )

    async def _update_repository_path(
        self,
        session: AsyncSession,
        workflow_id: str,
        repository_path: str,
    ) -> None:
        workflow = await session.get(WorkflowRun, workflow_id)
        if not workflow:
            return
        workflow.repository_path = repository_path

    async def update_review_report(
        self,
        workflow_id: str,
        review_report: ReviewReport,
        stage: str,
    ) -> bool:
        return await self._with_session(
            self._update_review_report,
            workflow_id,
            review_report,
            stage,
        )

    async def _update_review_report(
        self,
        session: AsyncSession,
        workflow_id: str,
        review_report: ReviewReport,
        stage: str,
    ) -> None:
        workflow = await session.get(WorkflowRun, workflow_id)
        if not workflow:
            return
        workflow.review_report = review_report.model_dump(mode="json")
        workflow.stage = stage

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

    async def get_workflow(self, workflow_id: str):
        from app.agents.workflow import WorkflowState
        from app.schemas.workflow import WorkflowStage, ApprovalStatus, ReviewReport
        from app.schemas.repository import RepositoryOverview, DifficultyEstimate
        from app.schemas.workflow import MentorExplanation, FixPlan, ConsensusReview
        from app.services.audit import AuditLogger, AuditRecord, MemoryAuditSink

        async with AsyncSessionLocal() as session:
            workflow_run = await session.get(WorkflowRun, workflow_id)
            if not workflow_run:
                return None

            sink = MemoryAuditSink()
            for event in (workflow_run.audit_events or []):
                rec = AuditRecord(
                    action=event.get("action", ""),
                    actor=event.get("actor", "system"),
                    status=event.get("status", "recorded"),
                    provider=event.get("provider"),
                    model=event.get("model"),
                    approval_id=event.get("approval_id"),
                    input_summary=event.get("input_summary"),
                    output_summary=event.get("output_summary"),
                    metadata=event.get("metadata") or {},
                )
                sink.records.append(rec)

            audit_logger = AuditLogger(sink=sink)

            state = WorkflowState(
                workflow_id=workflow_run.id,
                issue_url=workflow_run.issue_url,
                mode=workflow_run.mode,
                repository_path=workflow_run.repository_path,
                stage=WorkflowStage(workflow_run.stage),
                plan_approval=ApprovalStatus(workflow_run.plan_approval_status),
                final_approval=ApprovalStatus(workflow_run.final_approval_status),
                repository=RepositoryOverview.model_validate(workflow_run.repository)
                if workflow_run.repository
                else None,
                difficulty=DifficultyEstimate.model_validate(workflow_run.difficulty)
                if workflow_run.difficulty
                else None,
                mentor=MentorExplanation.model_validate(workflow_run.mentor)
                if workflow_run.mentor
                else None,
                plan=FixPlan.model_validate(workflow_run.plan) if workflow_run.plan else None,
                consensus=ConsensusReview.model_validate(workflow_run.consensus)
                if workflow_run.consensus
                else None,
                review_report=ReviewReport.model_validate(workflow_run.review_report)
                if workflow_run.review_report
                else None,
                audit=audit_logger,
            )
            return state

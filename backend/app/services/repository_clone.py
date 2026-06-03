from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError

from app.core.database import AsyncSessionLocal
from app.models.workflow import RepositoryCloneJob
from app.schemas.workflow import CloneRepositoryRequest, CloneRepositoryResponse
from app.services.audit import AuditLogger, AuditRecord
from app.tools.safe_executor import SafeToolExecutor


class RepositoryCloneError(ValueError):
    pass


@dataclass(slots=True)
class CloneTarget:
    repository_url: str
    target_name: str


class RepositoryCloneService:
    def __init__(self, executor: SafeToolExecutor | None = None) -> None:
        self.audit = AuditLogger()
        self.executor = executor or SafeToolExecutor(self.audit)

    async def clone(
        self,
        workflow_id: str,
        request: CloneRepositoryRequest,
    ) -> CloneRepositoryResponse:
        target = self._validate_target(str(request.repository_url), request.target_name)
        workspace = self.executor.workspace_root
        await self._ensure_workspace(workspace)
        target_path = self.executor.resolve_path(target.target_name)
        job_id = str(uuid4())

        await self.audit.record(
            AuditRecord(
                action="repository.clone.approved",
                actor=request.approved_by,
                approval_id=request.approved_by,
                input_summary=target.repository_url,
                metadata={"workflow_id": workflow_id, "target_path": str(target_path)},
            )
        )

        if target_path.exists():
            response = CloneRepositoryResponse(
                job_id=job_id,
                workflow_id=workflow_id,
                repository_url=target.repository_url,
                target_path=str(target_path),
                status="failed",
                approved_by=request.approved_by,
                exit_code=1,
                stderr="Target path already exists.",
            )
            await self._persist_job(response)
            return response

        result = await self.executor.run_command(
            [
                "git",
                "clone",
                "--depth",
                str(request.depth),
                target.repository_url,
                str(target_path),
            ],
            cwd=workspace,
            approved_by=request.approved_by,
        )
        response = CloneRepositoryResponse(
            job_id=job_id,
            workflow_id=workflow_id,
            repository_url=target.repository_url,
            target_path=str(target_path),
            status="completed" if result.exit_code == 0 else "failed",
            approved_by=request.approved_by,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
        )
        await self._persist_job(response)
        return response

    async def _ensure_workspace(self, workspace: Path) -> None:
        await asyncio.to_thread(workspace.mkdir, parents=True, exist_ok=True)

    async def _persist_job(self, response: CloneRepositoryResponse) -> bool:
        try:
            async with AsyncSessionLocal() as session:
                session.add(
                    RepositoryCloneJob(
                        id=response.job_id,
                        workflow_id=response.workflow_id,
                        repository_url=response.repository_url,
                        target_path=response.target_path,
                        status=response.status,
                        approved_by=response.approved_by,
                        stdout=response.stdout,
                        stderr=response.stderr,
                        exit_code=response.exit_code,
                    )
                )
                await session.commit()
            return True
        except (SQLAlchemyError, OSError):
            return False

    def _validate_target(self, repository_url: str, target_name: str | None) -> CloneTarget:
        parsed = urlparse(repository_url)
        if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
            raise RepositoryCloneError("Only HTTPS GitHub repository URLs are supported.")

        path = parsed.path.strip("/")
        parts = path.removesuffix(".git").split("/")
        if len(parts) != 2 or not all(parts):
            raise RepositoryCloneError(
                "Repository URL must look like https://github.com/owner/repo."
            )

        default_name = parts[1]
        selected_name = target_name or default_name
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", selected_name):
            raise RepositoryCloneError(
                "Target name may only contain letters, numbers, dots, dashes, and underscores."
            )

        clean_url = f"https://github.com/{parts[0]}/{parts[1]}.git"
        return CloneTarget(repository_url=clean_url, target_name=selected_name)

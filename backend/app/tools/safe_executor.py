from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings, get_settings
from app.services.audit import AuditLogger, AuditRecord


class PermissionDeniedError(RuntimeError):
    pass


@dataclass(slots=True)
class CommandResult:
    command: list[str]
    cwd: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


class SafeToolExecutor:
    def __init__(self, audit: AuditLogger, settings: Settings | None = None) -> None:
        self.audit = audit
        self.settings = settings or get_settings()
        self.workspace_root = self.settings.workspace_root

    def resolve_path(self, path: str | Path) -> Path:
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = self.workspace_root / candidate
        resolved = candidate.resolve()
        if resolved != self.workspace_root and self.workspace_root not in resolved.parents:
            raise PermissionDeniedError(f"path is outside workspace root: {resolved}")
        return resolved

    async def read_file(self, path: str | Path) -> str:
        resolved = self.resolve_path(path)
        await self.audit.record(
            AuditRecord(
                action="tool.file_read",
                input_summary=str(resolved),
                metadata={"path": str(resolved)},
            )
        )
        return await asyncio.to_thread(resolved.read_text, encoding="utf-8")

    async def write_file(self, path: str | Path, content: str, approved_by: str) -> None:
        resolved = self.resolve_path(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(resolved.write_text, content, encoding="utf-8")
        await self.audit.record(
            AuditRecord(
                action="tool.file_write",
                actor=approved_by,
                approval_id=approved_by,
                input_summary=str(resolved),
                metadata={"path": str(resolved), "bytes": len(content.encode())},
            )
        )

    async def run_command(
        self,
        command: list[str],
        cwd: str | Path | None = None,
        approved_by: str | None = None,
        command_timeout: int | None = None,
    ) -> CommandResult:
        if not command:
            raise ValueError("command must not be empty")

        resolved_cwd = self.resolve_path(cwd or self.workspace_root)
        timeout_seconds = command_timeout or self.settings.max_command_seconds
        await self.audit.record(
            AuditRecord(
                action="tool.terminal.start",
                actor=approved_by or "system",
                approval_id=approved_by,
                input_summary=" ".join(command),
                metadata={"cwd": str(resolved_cwd), "timeout": timeout_seconds},
            )
        )

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=resolved_cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            timed_out = False
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout_seconds
                )
            except TimeoutError:
                timed_out = True
                process.kill()
                stdout_bytes, stderr_bytes = await process.communicate()

            exit_code = process.returncode if process.returncode is not None else 124
        except NotImplementedError:
            # Windows event loop fallback for environments without subprocess support.
            timed_out, stdout_bytes, stderr_bytes, exit_code = await asyncio.to_thread(
                self._run_subprocess_blocking,
                command,
                resolved_cwd,
                timeout_seconds,
            )

        stdout = stdout_bytes.decode(errors="replace")[: self.settings.audit_stdout_limit]
        stderr = stderr_bytes.decode(errors="replace")[: self.settings.audit_stdout_limit]
        result = CommandResult(
            command=command,
            cwd=str(resolved_cwd),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            timed_out=timed_out,
        )
        await self.audit.record(
            AuditRecord(
                action="tool.terminal.finish",
                actor=approved_by or "system",
                approval_id=approved_by,
                status="timeout" if timed_out else "completed",
                output_summary=f"exit={result.exit_code}",
                metadata={"stdout": stdout, "stderr": stderr},
            )
        )
        return result

    def _run_subprocess_blocking(
        self,
        command: list[str],
        cwd: Path,
        timeout_seconds: int,
    ) -> tuple[bool, bytes, bytes, int]:
        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_seconds,
                check=False,
            )
            return False, completed.stdout or b"", completed.stderr or b"", completed.returncode
        except subprocess.TimeoutExpired as exc:
            return True, exc.stdout or b"", exc.stderr or b"", 124

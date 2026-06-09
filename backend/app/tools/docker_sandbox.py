import os
import time
import asyncio
import logging
from pathlib import Path
from pydantic import BaseModel

from app.core.config import get_settings
from app.services.audit import AuditLogger, AuditRecord
from app.tools.safe_executor import SafeToolExecutor

logger = logging.getLogger(__name__)

class SandboxResult(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    container_id: str
    audit_event_id: str | None = None

class DockerSandbox:
    def __init__(self, audit_logger: AuditLogger):
        self.audit = audit_logger
        self.settings = get_settings()
        self.workspace_root = Path(self.settings.workspace_root).resolve()
        self.socket_path = os.getenv("DOCKER_SOCKET_PATH")
        
        try:
            import docker
            if self.socket_path:
                self.client = docker.DockerClient(base_url=f"unix://{self.socket_path}")
            else:
                self.client = docker.from_env()
            self.client.ping()
            self.is_available = True
        except Exception as e:
            logger.warning(f"Docker unavailable: {e}. Falling back to SafeToolExecutor.")
            self.client = None
            self.is_available = False

    def validate_path(self, repo_path: Path) -> Path:
        rp = repo_path.resolve()
        rp_str = str(rp).lower()
        ws_str = str(self.workspace_root).lower()
        if not rp_str.startswith(ws_str):
            raise ValueError("Repository path must be within OSCA_WORKSPACE_ROOT")
        return rp

    async def run(self, repo_path: Path, command: str, timeout: int = 120) -> SandboxResult:
        rp = self.validate_path(repo_path)
        
        start_time = time.time()
        container_id = ""
        exit_code = -1
        stdout = ""
        stderr = ""
        
        if not self.is_available:
            logger.warning("Graceful degradation: Docker unavailable. Using SafeToolExecutor.")
            executor = SafeToolExecutor(self.audit, self.settings)
            
            cmd_list = ["bash", "-c", command]
            if os.name == "nt":
                cmd_list = ["cmd", "/c", command]
                
            res = await executor.run_command(cmd_list, cwd=rp, approved_by="docker_sandbox", command_timeout=timeout)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            audit_rec = AuditRecord(
                action="docker_sandbox",
                actor="docker_sandbox",
                status="completed_fallback",
                input_summary=command,
                output_summary=f"Exit: {res.exit_code}",
                metadata={"duration_ms": duration_ms, "fallback": True, "limits": "None"}
            )
            await self.audit.record(audit_rec)
            
            return SandboxResult(
                stdout=res.stdout,
                stderr=res.stderr,
                exit_code=res.exit_code,
                duration_ms=duration_ms,
                container_id="fallback",
                audit_event_id=None
            )
            
        import docker
        image = "python:3.11-slim"
        if (rp / "package.json").exists():
            image = "node:20-slim"
        elif (rp / "go.mod").exists():
            image = "golang:1.21"
            
        try:
            def _run():
                return self.client.containers.run(
                    image=image,
                    command=["sh", "-c", command],
                    volumes={
                        str(rp): {'bind': '/workspace', 'mode': 'ro'},
                    },
                    tmpfs={'/tmp/output': ''},
                    working_dir="/workspace",
                    mem_limit="512m",
                    cpu_period=100000,
                    cpu_quota=50000,
                    network_mode="none",
                    security_opt=["no-new-privileges:true"],
                    detach=True
                )
            
            container = await asyncio.to_thread(_run)
            container_id = container.id
            
            def _wait():
                try:
                    return container.wait(timeout=timeout)
                except Exception as e:
                    return {"Error": str(e), "StatusCode": 124}
                    
            wait_res = await asyncio.to_thread(_wait)
            exit_code = wait_res.get("StatusCode", 124)
            
            def _logs():
                try:
                    out = container.logs(stdout=True, stderr=False).decode("utf-8", "replace")
                    err = container.logs(stdout=False, stderr=True).decode("utf-8", "replace")
                    return out, err
                except:
                    return "", ""
                    
            stdout, stderr = await asyncio.to_thread(_logs)
            
            def _remove():
                try:
                    container.remove(force=True)
                except:
                    pass
            await asyncio.to_thread(_remove)
            
        except Exception as e:
            stderr = str(e)
            exit_code = 125
            
        duration_ms = int((time.time() - start_time) * 1000)
        
        audit_rec = AuditRecord(
            action="docker_sandbox",
            actor="docker_sandbox",
            status="completed",
            input_summary=command,
            output_summary=f"Exit: {exit_code}",
            metadata={"duration_ms": duration_ms, "image": image, "limits": "512m, 0.5cpu"}
        )
        await self.audit.record(audit_rec)
        
        return SandboxResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration_ms=duration_ms,
            container_id=container_id,
            audit_event_id=None
        )

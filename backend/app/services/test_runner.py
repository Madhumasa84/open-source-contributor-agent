from __future__ import annotations

from pathlib import Path

from app.tools.safe_executor import CommandResult, SafeToolExecutor
from pydantic import BaseModel
import re
import os

class TestExecutionEngine:
    def __init__(self, executor: SafeToolExecutor) -> None:
        self.executor = executor

    def detect_commands(self, root: str | Path) -> list[list[str]]:
        root_path = Path(root)
        commands: list[list[str]] = []
        if (root_path / "pyproject.toml").exists() or (root_path / "pytest.ini").exists():
            commands.append(["python", "-m", "pytest"])
        if (root_path / "package.json").exists():
            commands.append(["npm", "test", "--", "--runInBand"])
            commands.append(["npm", "run", "lint"])
        if (root_path / "go.mod").exists():
            commands.append(["go", "test", "./..."])
        if (root_path / "Cargo.toml").exists():
            commands.append(["cargo", "test"])
        return commands

    async def run(
        self, root: str | Path, approved_by: str, commands: list[list[str]] | None = None
    ) -> list[CommandResult]:
        selected = commands or self.detect_commands(root)
        results: list[CommandResult] = []
        for command in selected:
            results.append(
                await self.executor.run_command(command, cwd=root, approved_by=approved_by)
            )
        return results

class TestResult(BaseModel):
    passed: int = 0
    failed: int = 0
    errors: list[str] = []
    raw_output: str = ""

class TestRunnerService:
    def __init__(self, executor: SafeToolExecutor) -> None:
        self.executor = executor

    def detect_framework(self, root: str | Path) -> list[str]:
        root_path = Path(root)
        if (root_path / "pyproject.toml").exists() or (root_path / "pytest.ini").exists():
            return ["python", "-m", "pytest"]
        if (root_path / "package.json").exists():
            return ["npm", "test", "--", "--runInBand"]
        if (root_path / "go.mod").exists():
            return ["go", "test", "./..."]
        if (root_path / "Cargo.toml").exists():
            return ["cargo", "test"]
        return []

    async def run(self, repo_path: Path) -> TestResult:
        command = self.detect_framework(repo_path)
        if not command:
            return TestResult(errors=["No test framework detected"], raw_output="")
        
        use_docker = str(os.getenv("OSCA_USE_DOCKER_SANDBOX", "false")).lower() == "true"
        
        output = ""
        exit_code = -1
        timed_out = False
        
        if use_docker:
            from app.tools.docker_sandbox import DockerSandbox
            sandbox = DockerSandbox(self.executor.audit)
            if sandbox.is_available:
                cmd_str = " ".join(command)
                res = await sandbox.run(repo_path, cmd_str, timeout=120)
                output = res.stdout + "\n" + res.stderr
                exit_code = res.exit_code
                if res.exit_code in [124, 125]:
                    timed_out = True
            else:
                res = await self.executor.run_command(command, cwd=repo_path, approved_by="test_runner", command_timeout=120)
                output = res.stdout + "\n" + res.stderr
                exit_code = res.exit_code
                timed_out = res.timed_out
        else:
            res = await self.executor.run_command(command, cwd=repo_path, approved_by="test_runner", command_timeout=120)
            output = res.stdout + "\n" + res.stderr
            exit_code = res.exit_code
            timed_out = res.timed_out
        
        passed = 0
        failed = 0
        errors = []
        
        if exit_code != 0:
            errors.append(f"Command failed with exit code {exit_code}")
        if timed_out:
            errors.append("Test execution timed out")
            
        passed_matches = re.findall(r'(\d+)\s+passed', output, re.IGNORECASE)
        if passed_matches:
            passed = sum(int(m) for m in passed_matches)
            
        failed_matches = re.findall(r'(\d+)\s+failed', output, re.IGNORECASE)
        if failed_matches:
            failed = sum(int(m) for m in failed_matches)
            
        return TestResult(
            passed=passed,
            failed=failed,
            errors=errors,
            raw_output=output
        )

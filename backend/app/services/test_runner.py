from __future__ import annotations

from pathlib import Path

from app.tools.safe_executor import CommandResult, SafeToolExecutor


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

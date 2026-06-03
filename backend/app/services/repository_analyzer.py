from __future__ import annotations

import asyncio
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.schemas.repository import DifficultyLevel, RepositoryOverview

LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".md": "Markdown",
}

IGNORED_DIRS = {
    ".git",
    ".next",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    "node_modules",
    "target",
    "coverage",
}


class RepositoryAnalyzer:
    async def analyze(self, root: str | Path) -> RepositoryOverview:
        return await asyncio.to_thread(self._analyze_sync_from_input, root)

    def _analyze_sync_from_input(self, root: str | Path) -> RepositoryOverview:
        return self._analyze_sync(Path(root).expanduser().resolve())

    def _analyze_sync(self, root: Path) -> RepositoryOverview:
        if not root.exists() or not root.is_dir():
            raise FileNotFoundError(f"repository path does not exist: {root}")

        files = list(self._iter_files(root))
        language_counts = Counter(
            LANGUAGE_EXTENSIONS[file.suffix.lower()]
            for file in files
            if file.suffix.lower() in LANGUAGE_EXTENSIONS
        )
        dependencies = self._dependencies(root)
        frameworks = self._frameworks(root, dependencies)
        test_frameworks = self._test_frameworks(root, dependencies, files)
        build_systems = self._build_systems(root)
        important_files = self._important_files(root)
        entry_points = self._entry_points(root, files)
        risks = self._risks(files, dependencies, test_frameworks)
        metrics = self._quality_metrics(root, files)

        difficulty = DifficultyLevel.easy
        if len(files) > 400 or len(frameworks) > 3:
            difficulty = DifficultyLevel.hard
        elif len(files) > 120 or len(frameworks) > 1:
            difficulty = DifficultyLevel.medium

        return RepositoryOverview(
            root=str(root),
            languages=dict(language_counts),
            frameworks=frameworks,
            dependencies=dependencies,
            test_frameworks=test_frameworks,
            build_systems=build_systems,
            architecture=self._architecture(root, files),
            important_files=important_files,
            entry_points=entry_points,
            risks=risks,
            code_quality_metrics=metrics,
            contribution_difficulty=difficulty,
        )

    def _iter_files(self, root: Path) -> list[Path]:
        results: list[Path] = []
        for path in root.rglob("*"):
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            if path.is_file():
                results.append(path)
        return results

    def _dependencies(self, root: Path) -> dict[str, list[str]]:
        dependencies: dict[str, list[str]] = defaultdict(list)
        package_json = root / "package.json"
        if package_json.exists():
            data = self._read_json(package_json)
            for section in ("dependencies", "devDependencies"):
                dependencies["npm"].extend(sorted((data.get(section) or {}).keys()))

        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            dependencies["python"].append("pyproject.toml")

        requirements = root / "requirements.txt"
        if requirements.exists():
            dependencies["python"].extend(
                line.split("==")[0].strip()
                for line in requirements.read_text(encoding="utf-8", errors="ignore").splitlines()
                if line.strip() and not line.startswith("#")
            )

        if (root / "go.mod").exists():
            dependencies["go"].append("go.mod")
        if (root / "Cargo.toml").exists():
            dependencies["rust"].append("Cargo.toml")
        return dict(dependencies)

    def _frameworks(self, root: Path, dependencies: dict[str, list[str]]) -> list[str]:
        npm = set(dependencies.get("npm", []))
        python = set(dependencies.get("python", []))
        frameworks = []
        markers = {
            "Next.js": "next",
            "React": "react",
            "Vue": "vue",
            "Svelte": "svelte",
            "FastAPI": "fastapi",
            "Django": "django",
            "Flask": "flask",
            "SQLAlchemy": "sqlalchemy",
        }
        for name, dependency in markers.items():
            if dependency in npm or dependency in python:
                frameworks.append(name)
        if (root / "next.config.js").exists() or (root / "next.config.mjs").exists():
            frameworks.append("Next.js")
        return sorted(set(frameworks))

    def _test_frameworks(
        self,
        root: Path,
        dependencies: dict[str, list[str]],
        files: list[Path],
    ) -> list[str]:
        names = set()
        npm = set(dependencies.get("npm", []))
        python = set(dependencies.get("python", []))
        for dependency in ("pytest", "vitest", "jest", "playwright"):
            if dependency in npm or dependency in python:
                names.add(dependency)
        if (root / "pytest.ini").exists() or any(path.name.startswith("test_") for path in files):
            names.add("pytest")
        if any(path.name.endswith(".test.ts") or path.name.endswith(".spec.ts") for path in files):
            names.add("frontend tests")
        return sorted(names)

    def _build_systems(self, root: Path) -> list[str]:
        systems = []
        for marker, name in {
            "package.json": "npm",
            "pyproject.toml": "Python packaging",
            "Dockerfile": "Docker",
            "docker-compose.yml": "Docker Compose",
            "Makefile": "Make",
            "go.mod": "Go modules",
            "Cargo.toml": "Cargo",
        }.items():
            if (root / marker).exists():
                systems.append(name)
        return systems

    def _important_files(self, root: Path) -> list[str]:
        candidates = [
            "README.md",
            "CONTRIBUTING.md",
            "pyproject.toml",
            "package.json",
            "docker-compose.yml",
            ".github/workflows",
            "src",
            "app",
            "backend",
            "frontend",
        ]
        return [
            str((root / path).relative_to(root)) for path in candidates if (root / path).exists()
        ]

    def _entry_points(self, root: Path, files: list[Path]) -> list[str]:
        names = {"main.py", "app.py", "server.py", "index.ts", "index.tsx", "page.tsx", "main.go"}
        entry_points = [str(path.relative_to(root)) for path in files if path.name in names]
        return sorted(entry_points)[:20]

    def _architecture(self, root: Path, files: list[Path]) -> list[str]:
        top_level = sorted(
            {path.relative_to(root).parts[0] for path in files if path.relative_to(root).parts}
        )
        notes = [f"Top-level modules: {', '.join(top_level[:12]) or 'none'}"]
        if "backend" in top_level and "frontend" in top_level:
            notes.append("Monorepo with separated backend and frontend applications.")
        if "app" in top_level:
            notes.append("Application code is organized under an app directory.")
        if "tests" in top_level:
            notes.append("Repository includes a dedicated tests directory.")
        return notes

    def _risks(
        self,
        files: list[Path],
        dependencies: dict[str, list[str]],
        test_frameworks: list[str],
    ) -> list[str]:
        risks = []
        if not test_frameworks:
            risks.append("No test framework detected.")
        if len(files) > 600:
            risks.append("Large repository size may require narrower issue scoping.")
        if not dependencies:
            risks.append("Dependency metadata was not detected.")
        if any(path.name == ".env" for path in files):
            risks.append(
                "Environment file is present in repository tree; inspect for secret handling."
            )
        return risks or ["No immediate repository-level risks detected."]

    def _quality_metrics(self, root: Path, files: list[Path]) -> dict[str, Any]:
        code_files = [path for path in files if path.suffix.lower() in LANGUAGE_EXTENSIONS]
        test_files = [
            path for path in files if "test" in path.name.lower() or "spec" in path.name.lower()
        ]
        total_lines = 0
        for path in code_files[:1000]:
            try:
                total_lines += len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
            except OSError:
                continue
        return {
            "file_count": len(files),
            "code_file_count": len(code_files),
            "test_file_count": len(test_files),
            "test_to_code_ratio": round(len(test_files) / max(len(code_files), 1), 3),
            "sampled_lines": total_lines,
            "root": str(root),
        }

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

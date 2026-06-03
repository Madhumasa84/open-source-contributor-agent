from __future__ import annotations

import ast
from pathlib import Path

from app.schemas.repository import ImpactAnalysis, RiskLevel


class ImpactAnalyzer:
    def analyze_python_files(self, root: str | Path, relative_files: list[str]) -> ImpactAnalysis:
        root_path = Path(root).resolve()
        functions: list[str] = []
        classes: list[str] = []
        dependency_impact: list[str] = []

        for relative_file in relative_files:
            path = (root_path / relative_file).resolve()
            if path.suffix != ".py" or not path.exists():
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                dependency_impact.append(f"{relative_file}: parse failed")
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(f"{relative_file}:{node.name}")
                elif isinstance(node, ast.ClassDef):
                    classes.append(f"{relative_file}:{node.name}")
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    dependency_impact.append(relative_file)

        risk_level = RiskLevel.low
        if len(relative_files) > 8 or classes:
            risk_level = RiskLevel.medium
        if len(relative_files) > 20:
            risk_level = RiskLevel.high

        return ImpactAnalysis(
            files_modified=relative_files,
            functions_modified=sorted(set(functions)),
            classes_modified=sorted(set(classes)),
            dependency_impact=sorted(set(dependency_impact)),
            risk_level=risk_level,
        )

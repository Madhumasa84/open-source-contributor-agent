from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class DifficultyLevel(StrEnum):
    easy = "Easy"
    medium = "Medium"
    hard = "Hard"
    expert = "Expert"


class RiskLevel(StrEnum):
    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"


class RepositoryAnalyzeRequest(BaseModel):
    path: Path
    preferred_language: str = "en"


class RepositoryFileRequest(BaseModel):
    root: Path
    files: list[str] = Field(default_factory=list)


class RepositoryOverview(BaseModel):
    root: str
    languages: dict[str, int]
    frameworks: list[str]
    dependencies: dict[str, list[str]]
    test_frameworks: list[str]
    build_systems: list[str]
    architecture: list[str]
    important_files: list[str]
    entry_points: list[str]
    risks: list[str]
    code_quality_metrics: dict[str, Any]
    contribution_difficulty: DifficultyLevel


class DifficultyEstimate(BaseModel):
    level: DifficultyLevel
    files_impacted: int
    estimated_work: str
    confidence: float = Field(ge=0, le=1)
    rationale: list[str]


class SecurityFinding(BaseModel):
    rule: str
    file: str
    line: int
    severity: RiskLevel
    message: str


class SecurityReview(BaseModel):
    score: int = Field(ge=0, le=100)
    findings: list[SecurityFinding]
    summary: str


class ImpactAnalysis(BaseModel):
    files_modified: list[str]
    functions_modified: list[str]
    classes_modified: list[str]
    dependency_impact: list[str]
    risk_level: RiskLevel


class OnboardingGuide(BaseModel):
    architecture_overview: list[str]
    important_modules: list[str]
    build_instructions: list[str]
    development_workflow: list[str]
    good_first_issue_signals: list[str]
    learning_path: list[str]
    translation_warning: str | None = None


class GraphNode(BaseModel):
    id: str
    label: str
    type: str


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str


class RepositoryGraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class TestPlan(BaseModel):
    commands: list[list[str]]
    coverage_command: list[str] | None = None
    notes: list[str]

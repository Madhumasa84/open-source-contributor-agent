from app.schemas.repository import DifficultyLevel, RepositoryOverview
from app.schemas.workflow import FixPlan
from app.services.onboarding import ContributorOnboardingService
from app.services.pr_draft import PRDraftGenerator
from app.services.visualization import RepositoryVisualizationService


def make_overview() -> RepositoryOverview:
    return RepositoryOverview(
        root="/repo",
        languages={"Python": 3},
        frameworks=["FastAPI"],
        dependencies={"python": ["fastapi", "pytest"]},
        test_frameworks=["pytest"],
        build_systems=["Python packaging", "Docker Compose"],
        architecture=["Top-level modules: app, tests"],
        important_files=["README.md", "app/main.py"],
        entry_points=["app/main.py"],
        risks=["No immediate repository-level risks detected."],
        code_quality_metrics={"file_count": 5, "code_file_count": 3},
        contribution_difficulty=DifficultyLevel.easy,
    )


def test_onboarding_generates_build_and_learning_path():
    guide = ContributorOnboardingService().generate(make_overview())

    assert "pytest" in guide.build_instructions
    assert "app/main.py" in guide.important_modules
    assert guide.learning_path


def test_visualization_links_repository_to_frameworks_and_tests():
    graph = RepositoryVisualizationService().from_overview(make_overview())
    node_ids = {node.id for node in graph.nodes}

    assert "repo" in node_ids
    assert "framework:FastAPI" in node_ids
    assert "test:pytest" in node_ids
    assert graph.edges


def test_pr_draft_is_blocked_until_final_approval():
    plan = FixPlan(
        summary="Fix issue safely",
        root_cause="Boundary condition",
        proposed_steps=["Add regression test", "Patch implementation"],
        files_to_inspect=["app/main.py"],
        files_likely_changed=["app/main.py"],
        tests_to_run=["pytest"],
        risks=["Low risk"],
    )

    draft = PRDraftGenerator().generate("https://github.com/o/r/issues/1", plan)

    assert draft.ready_to_publish is False
    assert "Requires final human approval" in (draft.blocked_reason or "")
    assert "## Rollback Plan" in draft.body

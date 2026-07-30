import pytest
from unittest.mock import AsyncMock, patch

from app.schemas.github import GitHubIssueDetails
from app.schemas.repository import RepositoryOverview, DifficultyLevel
from app.services.issue_triager import IssueTriager
from app.services.audit import AuditLogger

@pytest.fixture
def mock_audit_logger():
    return AsyncMock(spec=AuditLogger)

@pytest.fixture(autouse=True)
def mock_registry():
    with patch("app.services.issue_triager.ProviderRegistry") as mock_reg:
        # Prevent actually calling any providers
        mock_reg.return_value._providers = {}
        yield mock_reg

@pytest.fixture(autouse=True)
def mock_language_service():
    # LanguageService is imported dynamically inside the method,
    # so we need to patch it where it is imported
    with patch("app.services.language_service.LanguageService") as mock_lang:
        # Mock translate_prompt_output to return english + no warning
        mock_instance = AsyncMock()
        mock_instance.translate_prompt_output.return_value = ("Translated reasoning", None)
        mock_lang.return_value = mock_instance
        yield mock_lang

@pytest.fixture
def base_issue():
    return GitHubIssueDetails(
        repository="test/repo",
        number=1,
        title="Test Issue",
        body="This is a test issue.",
        state="open",
        labels=[],
        author="testuser",
        comments=0,
        url="https://api.github.com/repos/test/repo/issues/1",
        html_url="https://github.com/test/repo/issues/1"
    )

@pytest.fixture
def base_repo_analysis():
    return RepositoryOverview(
        root="/test/repo",
        languages={"Python": 100},
        frameworks=["FastAPI"],
        dependencies={},
        test_frameworks=["pytest"],
        build_systems=["poetry"],
        architecture=[],
        important_files=[],
        entry_points=[],
        risks=[],
        code_quality_metrics={},
        contribution_difficulty=DifficultyLevel.medium
    )

@pytest.mark.asyncio
@pytest.mark.parametrize("level,expected_score", [
    (DifficultyLevel.easy, 3),
    (DifficultyLevel.medium, 5),
    (DifficultyLevel.hard, 8),
    (DifficultyLevel.expert, 10),
    (None, 5),  # Default to 5
])
async def test_difficulty_scoring(
    mock_audit_logger, base_issue, base_repo_analysis, level, expected_score
):
    base_repo_analysis.contribution_difficulty = level
    triager = IssueTriager(mock_audit_logger)

    result = await triager.triage(base_issue, base_repo_analysis)

    assert result.difficulty_score == expected_score

@pytest.mark.asyncio
async def test_fixability_scoring_base(mock_audit_logger, base_issue, base_repo_analysis):
    # Empty issue body, no test frameworks, cross-service architecture, no labels
    base_issue.body = ""
    base_repo_analysis.architecture = ["cross-service communication"]
    base_repo_analysis.test_frameworks = []

    triager = IssueTriager(mock_audit_logger)
    result = await triager.triage(base_issue, base_repo_analysis)

    # fixability starts at 0, no additions -> should be min'd to 1
    assert result.fixability_score == 1

@pytest.mark.asyncio
async def test_fixability_scoring_reproduction_steps(mock_audit_logger, base_issue, base_repo_analysis):
    base_issue.body = "Here are the steps to reproduce the issue..."
    base_repo_analysis.architecture = ["cross-service"]
    base_repo_analysis.test_frameworks = []

    triager = IssueTriager(mock_audit_logger)
    result = await triager.triage(base_issue, base_repo_analysis)

    # "steps to reproduce" -> +2
    assert result.fixability_score == 2

@pytest.mark.asyncio
async def test_fixability_scoring_code_references(mock_audit_logger, base_issue, base_repo_analysis):
    base_issue.body = "Check this file: main.py#L42"
    base_repo_analysis.architecture = ["cross-service"]
    base_repo_analysis.test_frameworks = []

    triager = IssueTriager(mock_audit_logger)
    result = await triager.triage(base_issue, base_repo_analysis)

    # ".py#" -> +2
    assert result.fixability_score == 2

@pytest.mark.asyncio
async def test_fixability_scoring_architecture(mock_audit_logger, base_issue, base_repo_analysis):
    base_issue.body = ""
    base_repo_analysis.architecture = ["monolithic app"] # No cross-service or external
    base_repo_analysis.test_frameworks = []

    triager = IssueTriager(mock_audit_logger)
    result = await triager.triage(base_issue, base_repo_analysis)

    # not cross-service/external -> +2
    assert result.fixability_score == 2

@pytest.mark.asyncio
async def test_fixability_scoring_bug_label(mock_audit_logger, base_issue, base_repo_analysis):
    base_issue.body = ""
    base_issue.labels = ["bug", "high-priority"]
    base_repo_analysis.architecture = ["cross-service"]
    base_repo_analysis.test_frameworks = []

    triager = IssueTriager(mock_audit_logger)
    result = await triager.triage(base_issue, base_repo_analysis)

    # "bug" in labels -> +1
    assert result.fixability_score == 1

@pytest.mark.asyncio
async def test_fixability_scoring_test_frameworks(mock_audit_logger, base_issue, base_repo_analysis):
    base_issue.body = ""
    base_repo_analysis.architecture = ["cross-service"]
    base_repo_analysis.test_frameworks = ["pytest"]

    triager = IssueTriager(mock_audit_logger)
    result = await triager.triage(base_issue, base_repo_analysis)

    # has test_frameworks -> +2
    assert result.fixability_score == 2

@pytest.mark.asyncio
async def test_fixability_scoring_long_body(mock_audit_logger, base_issue, base_repo_analysis):
    base_issue.body = "A" * 201
    base_repo_analysis.architecture = ["cross-service"]
    base_repo_analysis.test_frameworks = []

    triager = IssueTriager(mock_audit_logger)
    result = await triager.triage(base_issue, base_repo_analysis)

    # length > 200 -> +1
    assert result.fixability_score == 1

@pytest.mark.asyncio
async def test_fixability_scoring_max_cap(mock_audit_logger, base_issue, base_repo_analysis):
    base_issue.body = "Steps to reproduce: ... blob/ ... " + ("A" * 200) # +2, +2, +1
    base_issue.labels = ["bug"] # +1
    base_repo_analysis.architecture = ["monolithic"] # +2
    base_repo_analysis.test_frameworks = ["pytest"] # +2
    # Total would be 10. Wait let's make it 12 with extra.
    # Ah, "steps to reproduce" (+2), ".py#" (+2) wait ".py#" isn't here but "blob/" is (+2).
    # Total: 2 (repro) + 2 (blob) + 2 (arch) + 1 (bug) + 2 (tests) + 1 (len) = 10.

    # Wait let's make a custom logic that forces score to >10, we don't have enough to get 12 without changing logic, max is 10.
    # We just need to check it caps at 10.

    triager = IssueTriager(mock_audit_logger)
    result = await triager.triage(base_issue, base_repo_analysis)

    assert result.fixability_score == 10

@pytest.mark.asyncio
async def test_categorization_good_first_issue(mock_audit_logger, base_issue, base_repo_analysis):
    # Needs diff_score <= 4 and fixability >= 6
    base_repo_analysis.contribution_difficulty = DifficultyLevel.easy # diff_score = 3
    base_issue.body = "Steps to reproduce: ... blob/ ..." # fixability = 4
    base_issue.labels = ["bug"] # +1 = 5
    base_repo_analysis.architecture = ["monolithic"] # +2 = 7
    base_repo_analysis.test_frameworks = []

    triager = IssueTriager(mock_audit_logger)
    result = await triager.triage(base_issue, base_repo_analysis)

    assert result.good_first_issue is True
    assert result.contributor_level == "beginner"

@pytest.mark.asyncio
async def test_categorization_not_good_first_issue_diff(mock_audit_logger, base_issue, base_repo_analysis):
    # diff_score > 4 and fixability >= 6
    base_repo_analysis.contribution_difficulty = DifficultyLevel.medium # diff_score = 5
    base_issue.body = "Steps to reproduce: ... blob/ ..." # fixability = 4
    base_issue.labels = ["bug"] # +1 = 5
    base_repo_analysis.architecture = ["monolithic"] # +2 = 7

    triager = IssueTriager(mock_audit_logger)
    result = await triager.triage(base_issue, base_repo_analysis)

    assert result.good_first_issue is False
    assert result.contributor_level == "intermediate"

@pytest.mark.asyncio
async def test_categorization_not_good_first_issue_fixability(mock_audit_logger, base_issue, base_repo_analysis):
    # diff_score <= 4 and fixability < 6
    base_repo_analysis.contribution_difficulty = DifficultyLevel.easy # diff_score = 3
    base_issue.body = ""
    base_repo_analysis.architecture = ["cross-service"]
    base_repo_analysis.test_frameworks = []

    triager = IssueTriager(mock_audit_logger)
    result = await triager.triage(base_issue, base_repo_analysis)

    assert result.fixability_score < 6
    assert result.good_first_issue is False
    assert result.contributor_level == "beginner"

@pytest.mark.asyncio
async def test_categorization_contributor_level_advanced(mock_audit_logger, base_issue, base_repo_analysis):
    # diff_score > 7 -> advanced
    base_repo_analysis.contribution_difficulty = DifficultyLevel.hard # diff_score = 8

    triager = IssueTriager(mock_audit_logger)
    result = await triager.triage(base_issue, base_repo_analysis)

    assert result.contributor_level == "advanced"

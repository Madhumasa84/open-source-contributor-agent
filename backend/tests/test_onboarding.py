import pytest
from unittest.mock import AsyncMock, patch

from app.services.language_service import LanguageService
from app.schemas.repository import RepositoryOverview, DifficultyLevel
from app.services.onboarding import ContributorOnboardingService


@pytest.fixture
def service():
    return ContributorOnboardingService()


@pytest.fixture
def base_overview():
    return RepositoryOverview(
        root="/repo",
        languages={"Python": 100},
        frameworks=[],
        dependencies={},
        test_frameworks=[],
        build_systems=[],
        architecture=[],
        important_files=[],
        entry_points=[],
        risks=[],
        code_quality_metrics={},
        contribution_difficulty=DifficultyLevel.easy,
    )


@pytest.mark.asyncio
async def test_generate_empty_build_systems(service, base_overview):
    guide = await service.generate(base_overview)
    assert len(guide.build_instructions) == 1
    assert guide.build_instructions[0] == "Read README and dependency manifests before running commands."


@pytest.mark.asyncio
async def test_generate_npm_build_system(service, base_overview):
    base_overview.build_systems = ["npm"]
    guide = await service.generate(base_overview)
    assert "npm install" in guide.build_instructions
    assert "npm test" in guide.build_instructions
    assert "npm run lint" in guide.build_instructions
    assert len(guide.build_instructions) == 3


@pytest.mark.asyncio
async def test_generate_python_build_system(service, base_overview):
    base_overview.build_systems = ["Python packaging"]
    guide = await service.generate(base_overview)
    assert "python -m venv .venv" in guide.build_instructions
    assert "pip install -e .[dev]" in guide.build_instructions
    assert "pytest" in guide.build_instructions
    assert len(guide.build_instructions) == 3


@pytest.mark.asyncio
async def test_generate_docker_compose_build_system(service, base_overview):
    base_overview.build_systems = ["Docker Compose"]
    guide = await service.generate(base_overview)
    assert "docker compose up --build" in guide.build_instructions
    assert len(guide.build_instructions) == 1


@pytest.mark.asyncio
async def test_generate_multiple_build_systems(service, base_overview):
    base_overview.build_systems = ["npm", "Docker Compose"]
    guide = await service.generate(base_overview)
    assert "npm install" in guide.build_instructions
    assert "docker compose up --build" in guide.build_instructions
    assert len(guide.build_instructions) == 4


@pytest.mark.asyncio
async def test_important_modules_prioritizes_important_files(service, base_overview):
    base_overview.important_files = ["important1.py", "important2.py"]
    base_overview.entry_points = ["main.py", "cli.py"]
    guide = await service.generate(base_overview)
    assert guide.important_modules == ["important1.py", "important2.py"]


@pytest.mark.asyncio
async def test_important_modules_falls_back_to_entry_points(service, base_overview):
    base_overview.important_files = []
    base_overview.entry_points = ["main.py", "cli.py"]
    guide = await service.generate(base_overview)
    assert guide.important_modules == ["main.py", "cli.py"]


async def mock_translate_success(text, lang, ctx):
    return (f"TRANSLATED: {text}", None)


async def mock_translate_warning(text, lang, ctx):
    return (f"TRANSLATED: {text}", "Translation error")


@pytest.mark.asyncio
@patch("app.services.language_service.LanguageService.translate_prompt_output")
async def test_generate_with_translation(mock_translate, service, base_overview):
    mock_translate.side_effect = mock_translate_success

    guide = await service.generate(base_overview, preferred_language="es")

    assert guide.translation_warning is None
    assert mock_translate.called
    for item in guide.development_workflow:
        assert item.startswith("TRANSLATED: ")
    for item in guide.learning_path:
        assert item.startswith("TRANSLATED: ")


@pytest.mark.asyncio
@patch("app.services.language_service.LanguageService.translate_prompt_output")
async def test_generate_with_translation_warning(mock_translate, service, base_overview):
    mock_translate.side_effect = mock_translate_warning

    guide = await service.generate(base_overview, preferred_language="es")

    assert guide.translation_warning == "Translation error"

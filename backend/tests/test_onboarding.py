import pytest
from unittest.mock import AsyncMock, patch
import sys
import types
from app.services.onboarding import ContributorOnboardingService
from app.schemas.repository import RepositoryOverview, DifficultyLevel

@pytest.fixture
def onboarding_service():
    return ContributorOnboardingService()

def create_mock_overview(build_systems=None, important_files=None, entry_points=None):
    return RepositoryOverview(
        root="/fake/repo",
        languages={"Python": 100},
        frameworks=["FastAPI"],
        dependencies={"fastapi": ["0.100.0"]},
        test_frameworks=["pytest"],
        build_systems=build_systems or [],
        architecture=["REST API"],
        important_files=important_files or [],
        entry_points=entry_points or [],
        risks=[],
        code_quality_metrics={"coverage": 80},
        contribution_difficulty=DifficultyLevel.easy
    )

@pytest.mark.asyncio
async def test_generate_npm_build_system(onboarding_service):
    overview = create_mock_overview(build_systems=["npm"])
    guide = await onboarding_service.generate(overview)
    assert "npm install" in guide.build_instructions
    assert "npm test" in guide.build_instructions
    assert "npm run lint" in guide.build_instructions

@pytest.mark.asyncio
async def test_generate_python_build_system(onboarding_service):
    overview = create_mock_overview(build_systems=["Python packaging"])
    guide = await onboarding_service.generate(overview)
    assert "python -m venv .venv" in guide.build_instructions
    assert "pip install -e .[dev]" in guide.build_instructions
    assert "pytest" in guide.build_instructions

@pytest.mark.asyncio
async def test_generate_docker_build_system(onboarding_service):
    overview = create_mock_overview(build_systems=["Docker Compose"])
    guide = await onboarding_service.generate(overview)
    assert "docker compose up --build" in guide.build_instructions

@pytest.mark.asyncio
async def test_generate_no_build_system(onboarding_service):
    overview = create_mock_overview(build_systems=[])
    guide = await onboarding_service.generate(overview)
    assert len(guide.build_instructions) == 1
    assert "Read README and dependency manifests before running commands." in guide.build_instructions

@pytest.mark.asyncio
async def test_generate_important_modules_from_files(onboarding_service):
    overview = create_mock_overview(
        important_files=["main.py", "app.py"],
        entry_points=["entry.py"]
    )
    guide = await onboarding_service.generate(overview)
    assert guide.important_modules == ["main.py", "app.py"]

@pytest.mark.asyncio
async def test_generate_important_modules_from_entry_points(onboarding_service):
    overview = create_mock_overview(
        important_files=[],
        entry_points=["entry.py"]
    )
    guide = await onboarding_service.generate(overview)
    assert guide.important_modules == ["entry.py"]

# Provide a mock for both sys.modules to satisfy the deferred imports
@pytest.fixture(autouse=True)
def mock_deferred_imports():
    mock_lang_module = types.ModuleType("app.services.language_service")
    mock_audit_module = types.ModuleType("app.services.audit")

    sys.modules["app.services.language_service"] = mock_lang_module
    sys.modules["app.services.audit"] = mock_audit_module

    class FakeLanguageService:
        def __init__(self, audit_logger=None):
            self.translate_prompt_output = AsyncMock()

    class FakeAuditLogger:
        pass

    mock_lang_module.LanguageService = FakeLanguageService
    mock_audit_module.AuditLogger = FakeAuditLogger

    yield

    del sys.modules["app.services.language_service"]
    del sys.modules["app.services.audit"]

@pytest.mark.asyncio
async def test_generate_with_translation(onboarding_service):
    overview = create_mock_overview()

    with patch("app.services.language_service.LanguageService") as MockLangSvcClass:
        instance = MockLangSvcClass.return_value

        async def mock_translate(text, target, context):
            return f"Translated: {text}", "Some warning"

        instance.translate_prompt_output = AsyncMock(side_effect=mock_translate)

        with patch("app.services.audit.AuditLogger"):
            guide = await onboarding_service.generate(overview, preferred_language="es")

        assert instance.translate_prompt_output.call_count > 0

        assert all(item.startswith("Translated: ") for item in guide.development_workflow)
        assert all(item.startswith("Translated: ") for item in guide.learning_path)
        assert guide.translation_warning == "Some warning"

@pytest.mark.asyncio
async def test_generate_with_translation_no_warnings(onboarding_service):
    overview = create_mock_overview()

    with patch("app.services.language_service.LanguageService") as MockLangSvcClass:
        instance = MockLangSvcClass.return_value

        async def mock_translate(text, target, context):
            return f"Translated: {text}", None

        instance.translate_prompt_output = AsyncMock(side_effect=mock_translate)

        with patch("app.services.audit.AuditLogger"):
            guide = await onboarding_service.generate(overview, preferred_language="es")

        assert instance.translate_prompt_output.call_count > 0
        assert guide.translation_warning is None

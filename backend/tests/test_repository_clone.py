import pytest

from app.schemas.workflow import CloneRepositoryRequest
from app.services.repository_clone import RepositoryCloneError, RepositoryCloneService


def test_clone_service_normalizes_https_github_url():
    service = RepositoryCloneService()
    target = service._validate_target("https://github.com/openai/openai-python", None)

    assert target.repository_url == "https://github.com/openai/openai-python.git"
    assert target.target_name == "openai-python"


def test_clone_service_rejects_non_github_url():
    service = RepositoryCloneService()

    with pytest.raises(RepositoryCloneError):
        service._validate_target("https://example.com/openai/openai-python", None)


def test_clone_request_requires_human_actor():
    with pytest.raises(ValueError):
        CloneRepositoryRequest(
            repository_url="https://github.com/openai/openai-python",
            approved_by="",
        )

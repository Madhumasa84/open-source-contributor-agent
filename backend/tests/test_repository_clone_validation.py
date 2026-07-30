import pytest

from app.services.audit import AuditLogger, MemoryAuditSink
from app.services.repository_clone import RepositoryCloneError, RepositoryCloneService
from app.tools.safe_executor import SafeToolExecutor


def test_clone_service_validates_target_urls():
    executor = SafeToolExecutor(AuditLogger(sink=MemoryAuditSink()))
    service = RepositoryCloneService(executor)

    # Valid github urls
    target = service._validate_target("https://github.com/owner/repo.git", None)
    assert target.repository_url == "https://github.com/owner/repo.git"
    assert target.target_name == "repo"

    target2 = service._validate_target("https://github.com/owner/repo", "custom_name")
    assert target2.repository_url == "https://github.com/owner/repo.git"
    assert target2.target_name == "custom_name"

    # Invalid scheme / SSRF attempts
    with pytest.raises(RepositoryCloneError, match="HTTPS GitHub repository"):
        service._validate_target("http://github.com/owner/repo", None)

    with pytest.raises(RepositoryCloneError, match="HTTPS GitHub repository"):
        service._validate_target("git://github.com/owner/repo", None)

    with pytest.raises(RepositoryCloneError, match="HTTPS GitHub repository"):
        service._validate_target("file:///etc/passwd", None)

    with pytest.raises(RepositoryCloneError, match="HTTPS GitHub repository"):
        service._validate_target("https://localhost/owner/repo", None)

    with pytest.raises(RepositoryCloneError, match="HTTPS GitHub repository"):
        service._validate_target("https://127.0.0.1/owner/repo", None)

    with pytest.raises(RepositoryCloneError, match="HTTPS GitHub repository"):
        service._validate_target("https://gitlab.com/owner/repo", None)

    # Invalid path
    with pytest.raises(RepositoryCloneError, match="URL must look like"):
        service._validate_target("https://github.com/owner", None)

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.doc_drift import DocDriftDetector
from app.services.audit import AuditLogger, MemoryAuditSink

@pytest.fixture
def memory_audit():
    return AuditLogger(sink=MemoryAuditSink())

@pytest.fixture
def detector(memory_audit):
    return DocDriftDetector(memory_audit)

@pytest.mark.asyncio
async def test_empty_inputs(detector):
    # Empty patch_diff
    await detector.detect_and_report("https://github.com/foo/bar", "", ["src/main.py"])
    assert len(detector.audit.public_events()) == 0

    # Empty files_changed
    await detector.detect_and_report("https://github.com/foo/bar", "some diff\n" * 60, [])
    assert len(detector.audit.public_events()) == 0

@pytest.mark.asyncio
async def test_has_doc_changes(detector):
    patch_diff = "diff\n" * 60
    # Should not report if doc file changed
    await detector.detect_and_report("https://github.com/foo/bar", patch_diff, ["src/main.py", "README.md"])
    assert len(detector.audit.public_events()) == 0

    await detector.detect_and_report("https://github.com/foo/bar", patch_diff, ["docs/api.md"])
    assert len(detector.audit.public_events()) == 0

@pytest.mark.asyncio
async def test_small_patch(detector):
    patch_diff = "diff\n" * 49
    # Should not report if patch <= 50 lines
    await detector.detect_and_report("https://github.com/foo/bar", patch_diff, ["src/main.py"])
    assert len(detector.audit.public_events()) == 0


@pytest.mark.asyncio
async def test_no_token(detector):
    detector.bot.token = None
    patch_diff = "diff\n" * 60

    await detector.detect_and_report("https://github.com/foo/bar", patch_diff, ["src/main.py"])
    assert len(detector.audit.public_events()) == 0

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
async def test_create_issue(mock_post, detector):
    detector.bot.token = "fake-token"
    detector.bot.headers["Authorization"] = "Bearer fake-token"

    # Mocking successful API response
    mock_post.return_value.raise_for_status = MagicMock()

    patch_diff = "diff\n" * 60
    files = ["src/main.py", "src/utils.py"]

    await detector.detect_and_report("https://github.com/foo/bar", patch_diff, files)

    # Assert post was called correctly
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.github.com/repos/foo/bar/issues"
    assert kwargs["headers"] == detector.bot.headers
    assert "title" in kwargs["json"]
    assert "Update Documentation" in kwargs["json"]["title"]
    assert "src/main.py, src/utils.py" in kwargs["json"]["body"]

    # Assert audit log was recorded
    events = detector.audit.public_events()
    assert len(events) == 1
    event = events[0]
    assert event["action"] == "doc_drift.report"
    assert event["status"] == "completed"
    assert event["metadata"]["files"] == files

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
async def test_create_issue_api_failure(mock_post, detector):
    detector.bot.token = "fake-token"

    # Mocking API failure
    mock_post.return_value.raise_for_status = MagicMock(side_effect=Exception("API error"))

    patch_diff = "diff\n" * 60
    files = ["src/main.py"]

    # Should not raise, just log error
    await detector.detect_and_report("https://github.com/foo/bar", patch_diff, files)

    # Should not record audit log since it failed before audit log insertion
    assert len(detector.audit.public_events()) == 0

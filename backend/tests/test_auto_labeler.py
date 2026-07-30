import pytest
from unittest.mock import AsyncMock, patch

from app.services.auto_labeler import AutoIssueLabeler
from app.services.audit import AuditLogger, MemoryAuditSink
from app.schemas.repository import DifficultyEstimate, DifficultyLevel

@pytest.fixture
def memory_audit():
    return AuditLogger(sink=MemoryAuditSink())

@pytest.fixture
def labeler(memory_audit):
    return AutoIssueLabeler(memory_audit)

@pytest.mark.asyncio
async def test_label_mapping(labeler):
    easy = DifficultyEstimate(level=DifficultyLevel.easy, files_impacted=1, estimated_work="1h", confidence=0.8, rationale=[])
    labels = labeler._map_labels(easy, {"is_bug": True})
    assert "difficulty:easy" in labels
    assert "good-first-issue" in labels
    assert "bug" in labels

    hard = DifficultyEstimate(level=DifficultyLevel.hard, files_impacted=1, estimated_work="1h", confidence=0.8, rationale=[])
    labels = labeler._map_labels(hard, {})
    assert "difficulty:hard" in labels
    assert "good-first-issue" not in labels

@pytest.mark.asyncio
@patch("os.getenv", return_value="false")
async def test_label_issue_disabled(mock_getenv, labeler):
    with patch.object(labeler.bot, "apply_labels", new_callable=AsyncMock) as mock_apply:
        easy = DifficultyEstimate(level=DifficultyLevel.easy, files_impacted=1, estimated_work="1h", confidence=0.8, rationale=[])
        await labeler.label_issue("wf-1", "https://github.com/foo/bar/issues/1", easy)

        mock_apply.assert_not_called()

        # Check no audit event for auto_labeler
        events = labeler.audit.public_events()
        assert not any(e["action"] == "issue.auto_labeled" for e in events)

@pytest.mark.asyncio
@patch("os.getenv", return_value="true")
async def test_label_issue_enabled(mock_getenv, labeler):
    with patch.object(labeler.bot, "apply_labels", new_callable=AsyncMock) as mock_apply:
        easy = DifficultyEstimate(level=DifficultyLevel.easy, files_impacted=1, estimated_work="1h", confidence=0.8, rationale=[])
        await labeler.label_issue("wf-1", "https://github.com/foo/bar/issues/1", easy)

        mock_apply.assert_called_once_with("https://github.com/foo/bar/issues/1", ["difficulty:easy", "good-first-issue"])

        # Check audit event
        events = labeler.audit.public_events()
        assert len(events) == 1
        assert events[0]["action"] == "issue.auto_labeled"
        assert events[0]["metadata"]["labels"] == ["difficulty:easy", "good-first-issue"]

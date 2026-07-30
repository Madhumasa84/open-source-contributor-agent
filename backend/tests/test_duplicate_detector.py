from unittest.mock import MagicMock

import pytest

from app.services.audit import AuditLogger, MemoryAuditSink
from app.services.duplicate_detector import DuplicateIssueDetector


@pytest.fixture
def memory_audit():
    return AuditLogger(sink=MemoryAuditSink())

@pytest.fixture
def detector(memory_audit):
    return DuplicateIssueDetector(memory_audit)

@pytest.mark.asyncio
async def test_duplicate_detection(detector, monkeypatch):
    # Mock indexer embedding
    async def mock_get_embedding(text):
        return [0.1, 0.2, 0.3]
    monkeypatch.setattr(detector.indexer, "get_embedding", mock_get_embedding)

    # Mock cosine similarity to return > 0.85
    monkeypatch.setattr(detector.indexer, "cosine_similarity", lambda a, b: 0.90)

    # Mock database session
    mock_row = MagicMock()
    mock_row.url = "https://github.com/foo/bar/issues/100"
    mock_row.summary = "Similar issue"
    mock_row.embedding = "[0.1, 0.2, 0.3]"

    class MockResult:
        def fetchall(self):
            return [mock_row]

    class MockSession:
        async def execute(self, *args, **kwargs):
            return MockResult()
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr("app.services.duplicate_detector.AsyncSessionLocal", MockSession)

    candidates = await detector.detect_duplicates("New issue", "https://github.com/foo/bar/issues/200", "wf-1")

    assert len(candidates) == 1
    assert candidates[0]["url"] == "https://github.com/foo/bar/issues/100"
    assert candidates[0]["similarity"] == 0.90

    # Ensure it was logged but not auto-closed
    events = detector.audit.public_events()
    assert len(events) == 1
    assert events[0]["action"] == "issue.duplicate_detected"
    assert events[0]["metadata"]["candidates"][0]["url"] == "https://github.com/foo/bar/issues/100"

@pytest.mark.asyncio
async def test_duplicate_detection_below_threshold(detector, monkeypatch):
    # Mock indexer embedding
    async def mock_get_embedding(text):
        return [0.1, 0.2, 0.3]
    monkeypatch.setattr(detector.indexer, "get_embedding", mock_get_embedding)

    # Mock cosine similarity to return <= 0.85
    monkeypatch.setattr(detector.indexer, "cosine_similarity", lambda a, b: 0.80)

    # Mock database session
    mock_row = MagicMock()
    mock_row.url = "https://github.com/foo/bar/issues/100"
    mock_row.summary = "Similar issue"
    mock_row.embedding = "[0.1, 0.2, 0.3]"

    class MockResult:
        def fetchall(self):
            return [mock_row]

    class MockSession:
        async def execute(self, *args, **kwargs):
            return MockResult()
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr("app.services.duplicate_detector.AsyncSessionLocal", MockSession)

    candidates = await detector.detect_duplicates("New issue", "https://github.com/foo/bar/issues/200", "wf-1")

    assert len(candidates) == 0

    # Ensure no audit event logged
    events = detector.audit.public_events()
    assert len(events) == 0

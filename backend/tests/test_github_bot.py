import json
import pytest
import httpx
import respx
from unittest.mock import patch, AsyncMock

from app.services.github_bot import GitHubBot
from app.services.audit import AuditLogger, MemoryAuditSink

@pytest.fixture
def memory_audit():
    return AuditLogger(sink=MemoryAuditSink())

@pytest.fixture
@patch("app.services.github_bot.get_settings")
def github_bot(mock_get_settings, memory_audit):
    mock_settings = mock_get_settings.return_value
    mock_settings.github_token = "fake-token"
    return GitHubBot(memory_audit)

@pytest.fixture
@patch("app.services.github_bot.get_settings")
def no_token_bot(mock_get_settings, memory_audit):
    mock_settings = mock_get_settings.return_value
    mock_settings.github_token = None
    return GitHubBot(memory_audit)

def test_parse_issue_url(github_bot):
    owner, repo, issue_number = github_bot._parse_issue_url("https://github.com/expressjs/express/issues/5747")
    assert owner == "expressjs"
    assert repo == "express"
    assert issue_number == "5747"

    owner, repo, issue_number = github_bot._parse_issue_url("https://github.com/expressjs/express/issues/5747/")
    assert owner == "expressjs"
    assert repo == "express"
    assert issue_number == "5747"

@pytest.mark.asyncio
@respx.mock
async def test_apply_labels_happy_path(github_bot):
    url = "https://api.github.com/repos/expressjs/express/issues/5747/labels"
    route = respx.post(url).mock(return_value=httpx.Response(200, json={}))

    await github_bot.apply_labels("https://github.com/expressjs/express/issues/5747", ["bug", "easy"])

    assert route.called
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer fake-token"
    assert json.loads(request.content) == {"labels": ["bug", "easy"]}

    events = github_bot.audit.public_events()
    assert len(events) == 1
    assert events[0]["action"] == "github_apply_labels"
    assert events[0]["metadata"]["labels"] == ["bug", "easy"]

@pytest.mark.asyncio
@respx.mock
async def test_apply_labels_no_token(no_token_bot):
    url = "https://api.github.com/repos/expressjs/express/issues/5747/labels"
    route = respx.post(url).mock(return_value=httpx.Response(200, json={}))

    with patch("app.services.github_bot.logger") as mock_logger:
        await no_token_bot.apply_labels("https://github.com/expressjs/express/issues/5747", ["bug", "easy"])
        mock_logger.warning.assert_called_once()

    assert not route.called
    assert len(no_token_bot.audit.public_events()) == 0

@pytest.mark.asyncio
@respx.mock
async def test_apply_labels_httpx_exception(github_bot):
    url = "https://api.github.com/repos/expressjs/express/issues/5747/labels"
    route = respx.post(url).mock(return_value=httpx.Response(500, json={}))

    with patch("app.services.github_bot.logger") as mock_logger:
        await github_bot.apply_labels("https://github.com/expressjs/express/issues/5747", ["bug", "easy"])
        mock_logger.error.assert_called_once()

    assert route.called
    assert len(github_bot.audit.public_events()) == 0

@pytest.mark.asyncio
@respx.mock
async def test_post_comment_happy_path(github_bot):
    url = "https://api.github.com/repos/expressjs/express/issues/5747/comments"
    route = respx.post(url).mock(return_value=httpx.Response(201, json={}))

    await github_bot.post_comment("https://github.com/expressjs/express/issues/5747", "Hello, world!")

    assert route.called
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer fake-token"
    assert json.loads(request.content) == {"body": "Hello, world!"}

    events = github_bot.audit.public_events()
    assert len(events) == 1
    assert events[0]["action"] == "github_post_comment"
    assert events[0]["metadata"]["issue"] == "https://github.com/expressjs/express/issues/5747"

@pytest.mark.asyncio
@respx.mock
async def test_post_comment_no_token(no_token_bot):
    url = "https://api.github.com/repos/expressjs/express/issues/5747/comments"
    route = respx.post(url).mock(return_value=httpx.Response(201, json={}))

    with patch("app.services.github_bot.logger") as mock_logger:
        await no_token_bot.post_comment("https://github.com/expressjs/express/issues/5747", "Hello, world!")
        mock_logger.warning.assert_called_once()

    assert not route.called
    assert len(no_token_bot.audit.public_events()) == 0

@pytest.mark.asyncio
@respx.mock
async def test_post_comment_httpx_exception(github_bot):
    url = "https://api.github.com/repos/expressjs/express/issues/5747/comments"
    route = respx.post(url).mock(return_value=httpx.Response(500, json={}))

    with patch("app.services.github_bot.logger") as mock_logger:
        await github_bot.post_comment("https://github.com/expressjs/express/issues/5747", "Hello, world!")
        mock_logger.error.assert_called_once()

    assert route.called
    assert len(github_bot.audit.public_events()) == 0

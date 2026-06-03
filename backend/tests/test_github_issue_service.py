import pytest

from app.services.github_issues import GitHubIssueError, GitHubIssueService


def test_parse_issue_url_accepts_issues():
    reference = GitHubIssueService().parse_issue_url(
        "https://github.com/octo-org/octo-repo/issues/42"
    )

    assert reference.owner == "octo-org"
    assert reference.repo == "octo-repo"
    assert reference.number == 42
    assert reference.kind == "issues"


def test_parse_issue_url_accepts_pull_requests():
    reference = GitHubIssueService().parse_issue_url(
        "https://github.com/octo-org/octo-repo/pull/99"
    )

    assert reference.kind == "pull"
    assert reference.number == 99


def test_parse_issue_url_rejects_non_github():
    with pytest.raises(GitHubIssueError):
        GitHubIssueService().parse_issue_url("https://example.com/octo/repo/issues/1")


def test_parse_issue_url_rejects_invalid_path():
    with pytest.raises(GitHubIssueError):
        GitHubIssueService().parse_issue_url("https://github.com/octo/repo")

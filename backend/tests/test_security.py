import pytest
from pathlib import Path

from app.schemas.repository import RiskLevel
from app.services.security import SecurityReviewer


def test_security_reviewer_clean_file(tmp_path: Path):
    reviewer = SecurityReviewer()
    file_path = tmp_path / "clean.py"
    file_path.write_text("print('hello world')", encoding="utf-8")

    review = reviewer.review_files(tmp_path, ["clean.py"])

    assert review.score == 100
    assert len(review.findings) == 0
    assert review.summary == "No security issues detected."


def test_security_reviewer_hardcoded_secret(tmp_path: Path):
    reviewer = SecurityReviewer()
    file_path = tmp_path / "secret.py"
    file_path.write_text("api_key = \"123456789\"", encoding="utf-8")

    review = reviewer.review_files(tmp_path, ["secret.py"])

    assert len(review.findings) == 1
    finding = review.findings[0]
    assert finding.rule == "hardcoded-secret"
    assert finding.severity == RiskLevel.high
    assert finding.line == 1
    assert finding.file == "secret.py"
    assert review.score < 100
    assert "security finding(s) detected" in review.summary


def test_security_reviewer_path_traversal(tmp_path: Path):
    reviewer = SecurityReviewer()
    file_path = tmp_path / "path.py"
    file_path.write_text("file = open('../../etc/passwd')", encoding="utf-8")

    review = reviewer.review_files(tmp_path, ["path.py"])

    assert len(review.findings) == 1
    finding = review.findings[0]
    assert finding.rule == "path-traversal"
    assert finding.severity == RiskLevel.medium


def test_security_reviewer_command_injection(tmp_path: Path):
    reviewer = SecurityReviewer()
    file_path = tmp_path / "cmd.py"
    file_path.write_text("import os\nos.system('rm -rf /')", encoding="utf-8")

    review = reviewer.review_files(tmp_path, ["cmd.py"])

    assert len(review.findings) == 1
    finding = review.findings[0]
    assert finding.rule == "command-injection"
    assert finding.severity == RiskLevel.high


def test_security_reviewer_sql_injection(tmp_path: Path):
    reviewer = SecurityReviewer()
    file_path = tmp_path / "sql.py"
    file_path.write_text("execute(f'SELECT * FROM users WHERE id = {user_id}')", encoding="utf-8")

    review = reviewer.review_files(tmp_path, ["sql.py"])

    assert len(review.findings) == 1
    finding = review.findings[0]
    assert finding.rule == "sql-injection"
    assert finding.severity == RiskLevel.high


def test_security_reviewer_auth_bypass(tmp_path: Path):
    reviewer = SecurityReviewer()
    file_path = tmp_path / "auth.py"
    file_path.write_text("is_admin = True", encoding="utf-8")

    review = reviewer.review_files(tmp_path, ["auth.py"])

    assert len(review.findings) == 1
    finding = review.findings[0]
    assert finding.rule == "auth-bypass"
    assert finding.severity == RiskLevel.critical


def test_security_reviewer_unsafe_path(tmp_path: Path):
    reviewer = SecurityReviewer()

    # Try to access a file outside the tmp_path root
    review = reviewer.review_files(tmp_path, ["../outside.py"])

    assert len(review.findings) == 1
    finding = review.findings[0]
    assert finding.rule == "unsafe-path"
    assert finding.severity == RiskLevel.critical
    assert finding.message == "Requested file is outside repository root."


def test_security_reviewer_nonexistent_file(tmp_path: Path):
    reviewer = SecurityReviewer()

    # File doesn't exist, should be ignored
    review = reviewer.review_files(tmp_path, ["does_not_exist.py"])

    assert review.score == 100
    assert len(review.findings) == 0

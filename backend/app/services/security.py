from __future__ import annotations

import re
from pathlib import Path

from app.schemas.repository import RiskLevel, SecurityFinding, SecurityReview

SECURITY_PATTERNS = [
    (
        "hardcoded-secret",
        re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*=\s*['\"][^'\"]{8,}['\"]"),
        RiskLevel.high,
        "Possible hardcoded credential.",
    ),
    (
        "path-traversal",
        re.compile(r"\.\./|\.\.\\\\"),
        RiskLevel.medium,
        "Path traversal token detected.",
    ),
    (
        "command-injection",
        re.compile(r"(?i)(shell=True|os\.system|subprocess\.(call|run|popen).*\+\s*)"),
        RiskLevel.high,
        "Potential command injection sink.",
    ),
    (
        "sql-injection",
        re.compile(r"(?i)(execute|query)\(.*(%|\+|f['\"])", re.MULTILINE),
        RiskLevel.high,
        "Potential string-built SQL query.",
    ),
    (
        "auth-bypass",
        re.compile(r"(?i)(disable_auth|skip_auth|is_admin\s*=\s*true)"),
        RiskLevel.critical,
        "Authentication or authorization bypass marker.",
    ),
]


class SecurityReviewer:
    def review_files(self, root: str | Path, relative_files: list[str]) -> SecurityReview:
        root_path = Path(root).resolve()
        findings: list[SecurityFinding] = []

        for relative_file in relative_files:
            path = (root_path / relative_file).resolve()
            if root_path not in path.parents and path != root_path:
                findings.append(
                    SecurityFinding(
                        rule="unsafe-path",
                        file=relative_file,
                        line=0,
                        severity=RiskLevel.critical,
                        message="Requested file is outside repository root.",
                    )
                )
                continue
            if not path.exists() or not path.is_file():
                continue

            text = path.read_text(encoding="utf-8", errors="ignore")
            for line_no, line in enumerate(text.splitlines(), start=1):
                for rule, pattern, severity, message in SECURITY_PATTERNS:
                    if pattern.search(line):
                        findings.append(
                            SecurityFinding(
                                rule=rule,
                                file=relative_file,
                                line=line_no,
                                severity=severity,
                                message=message,
                            )
                        )

        penalty = sum(
            {"Low": 2, "Medium": 8, "High": 18, "Critical": 35}[finding.severity.value]
            for finding in findings
        )
        score = max(0, 100 - penalty)
        summary = (
            "No security issues detected."
            if not findings
            else f"{len(findings)} security finding(s) detected."
        )
        return SecurityReview(score=score, findings=findings, summary=summary)

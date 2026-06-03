from app.schemas.review import PRDraft, ReviewReport
from app.schemas.workflow import FixPlan


class PRDraftGenerator:
    def generate(
        self,
        issue_url: str,
        plan: FixPlan,
        review_report: ReviewReport | None = None,
        final_approved: bool = False,
    ) -> PRDraft:
        files = review_report.files_changed if review_report else plan.files_likely_changed
        tests = review_report.tests_run if review_report else plan.tests_to_run
        security = (
            review_report.security_review.summary
            if review_report and review_report.security_review
            else "Security review pending."
        )
        risks = review_report.risk_assessment if review_report else plan.risks
        body = "\n".join(
            [
                "## Summary",
                plan.summary,
                "",
                "## Root Cause",
                review_report.root_cause if review_report else plan.root_cause,
                "",
                "## Solution",
                "\n".join(f"- {step}" for step in plan.proposed_steps),
                "",
                "## Files Modified",
                "\n".join(f"- {file}" for file in files) or "- None yet",
                "",
                "## Tests",
                "\n".join(f"- {test}" for test in tests) or "- Pending",
                "",
                "## Coverage",
                review_report.coverage if review_report and review_report.coverage else "Pending",
                "",
                "## Security Notes",
                security,
                "",
                "## Risks",
                "\n".join(f"- {risk}" for risk in risks) or "- No known risks",
                "",
                "## Rollback Plan",
                "Revert the generated commit and rerun the affected tests.",
                "",
                f"Closes: {issue_url}",
            ]
        )
        return PRDraft(
            title=plan.summary[:120],
            body=body,
            labels=["ai-assisted", "needs-human-review"],
            ready_to_publish=final_approved,
            blocked_reason=None
            if final_approved
            else "Requires final human approval before GitHub PR creation.",
        )

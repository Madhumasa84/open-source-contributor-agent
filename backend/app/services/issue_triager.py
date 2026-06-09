import hashlib
from typing import Literal
from pydantic import BaseModel

from app.schemas.github import GitHubIssueDetails
from app.schemas.repository import RepositoryOverview
from app.services.audit import AuditLogger, AuditRecord
from app.ai.providers.registry import ProviderRegistry
from app.schemas.provider import ModelRequest, ChatMessage

# Aliases to match exact names requested by prompt
GitHubIssue = GitHubIssueDetails
RepoAnalysis = RepositoryOverview


class TriageResult(BaseModel):
    difficulty_score: int
    fixability_score: int
    suggested_entry_points: list[str]
    good_first_issue: bool
    contributor_level: Literal["beginner", "intermediate", "advanced"]
    triage_reasoning: str
    translation_warning: str | None = None


class IssueTriager:
    def __init__(self, audit_logger: AuditLogger):
        self.audit = audit_logger

    async def triage(self, issue: GitHubIssue, repo_analysis: RepoAnalysis, preferred_language: str = "en") -> TriageResult:
        difficulty_map = {
            "Easy": 3,
            "Medium": 5,
            "Hard": 8,
            "Expert": 10
        }
        diff_score = difficulty_map.get(repo_analysis.contribution_difficulty.value if repo_analysis.contribution_difficulty else "Medium", 5)

        fixability = 0
        body_lower = issue.body.lower() if issue.body else ""
        
        if "steps to reproduce" in body_lower or "reproduction" in body_lower:
            fixability += 2
            
        if "blob/" in body_lower or ".py#" in body_lower or ".ts#" in body_lower or ".js#" in body_lower:
            fixability += 2
            
        if not any("cross-service" in r.lower() or "external" in r.lower() for r in getattr(repo_analysis, "architecture", [])):
            fixability += 2
            
        if any("bug" in label.lower() for label in issue.labels):
            fixability += 1
            
        if getattr(repo_analysis, "test_frameworks", []):
            fixability += 2
            
        if len(issue.body or "") > 200:
            fixability += 1
            
        fixability = min(10, max(1, fixability))
        
        good_first_issue = (diff_score <= 4 and fixability >= 6)
        
        if diff_score <= 4:
            contributor_level = "beginner"
        elif diff_score <= 7:
            contributor_level = "intermediate"
        else:
            contributor_level = "advanced"
            
        prompt = (
            f"Explain these triage scores in 2-3 sentences: "
            f"Difficulty={diff_score}/10, Fixability={fixability}/10. "
            f"Issue: {issue.title}. Repo tests: {getattr(repo_analysis, 'test_frameworks', [])}."
        )
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        reasoning = f"Triage scores generated. Difficulty: {diff_score}, Fixability: {fixability}."
        
        registry = ProviderRegistry()
        for provider_name, provider_inst in registry._providers.items():
            descriptor = provider_inst.descriptor()
            if descriptor.configured:
                try:
                    request = ModelRequest(
                        model=descriptor.default_models[0],
                        messages=[ChatMessage(role="user", content=prompt)],
                        max_tokens=150
                    )
                    response = await provider_inst.complete(request)
                    reasoning = response.content
                    break
                except Exception:
                    continue
        
        await self.audit.record(AuditRecord(
            action="issue_triage",
            actor="issue_triager",
            status="completed",
            prompt=prompt,
            input_summary=prompt_hash,
            output_summary=f"Diff: {diff_score}, Fix: {fixability}",
            metadata={"difficulty": diff_score, "fixability": fixability}
        ))
        
        from app.services.language_service import LanguageService
        lang_svc = LanguageService(self.audit)
        translated_reasoning, warning = await lang_svc.translate_prompt_output(reasoning, preferred_language, "triage_reasoning")

        return TriageResult(
            difficulty_score=diff_score,
            fixability_score=fixability,
            suggested_entry_points=repo_analysis.entry_points if hasattr(repo_analysis, 'entry_points') else [],
            good_first_issue=good_first_issue,
            contributor_level=contributor_level,
            triage_reasoning=translated_reasoning,
            translation_warning=warning
        )

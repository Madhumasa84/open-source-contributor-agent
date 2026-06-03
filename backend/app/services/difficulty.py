from app.schemas.repository import DifficultyEstimate, DifficultyLevel, RepositoryOverview


class DifficultyEstimator:
    def estimate(
        self,
        issue_summary: str | None,
        repository: RepositoryOverview | None,
    ) -> DifficultyEstimate:
        text = (issue_summary or "").lower()
        rationale: list[str] = []
        score = 0

        if any(word in text for word in ("typo", "docs", "readme", "copy")):
            score += 1
            rationale.append("Issue text suggests a documentation or copy-only change.")
        if any(word in text for word in ("bug", "fix", "regression")):
            score += 2
            rationale.append("Issue likely requires behavior investigation.")
        if any(word in text for word in ("security", "auth", "race", "data loss", "migration")):
            score += 4
            rationale.append("Issue mentions high-risk implementation areas.")

        files_impacted = 1
        if repository:
            file_count = repository.code_quality_metrics.get("code_file_count", 0)
            if file_count > 400:
                score += 3
                rationale.append("Repository has a large code surface.")
            elif file_count > 100:
                score += 2
                rationale.append("Repository has a moderate code surface.")
            if repository.risks and repository.risks != [
                "No immediate repository-level risks detected."
            ]:
                score += 1
                rationale.append("Repository analyzer detected contribution risks.")
            files_impacted = 2 if repository.entry_points else 1

        if score <= 2:
            level = DifficultyLevel.easy
            estimated_work = "1-3 hours"
            confidence = 0.64
        elif score <= 4:
            level = DifficultyLevel.medium
            estimated_work = "Half day to 1 day"
            confidence = 0.58
            files_impacted = max(files_impacted, 3)
        elif score <= 6:
            level = DifficultyLevel.hard
            estimated_work = "1-3 days"
            confidence = 0.52
            files_impacted = max(files_impacted, 5)
        else:
            level = DifficultyLevel.expert
            estimated_work = "Several days"
            confidence = 0.45
            files_impacted = max(files_impacted, 8)

        if not rationale:
            rationale.append("Estimate is based on repository size and limited issue context.")

        return DifficultyEstimate(
            level=level,
            files_impacted=files_impacted,
            estimated_work=estimated_work,
            confidence=confidence,
            rationale=rationale,
        )

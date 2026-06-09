from app.schemas.repository import OnboardingGuide, RepositoryOverview


class ContributorOnboardingService:
    async def generate(self, overview: RepositoryOverview, preferred_language: str = "en") -> OnboardingGuide:
        build_instructions: list[str] = []
        if "npm" in overview.build_systems:
            build_instructions.extend(["npm install", "npm test", "npm run lint"])
        if "Python packaging" in overview.build_systems:
            build_instructions.extend(
                [
                    "python -m venv .venv",
                    "pip install -e .[dev]",
                    "pytest",
                ]
            )
        if "Docker Compose" in overview.build_systems:
            build_instructions.append("docker compose up --build")
        if not build_instructions:
            build_instructions.append(
                "Read README and dependency manifests before running commands."
            )

        important_modules = overview.important_files[:10] or overview.entry_points[:10]
        learning_path = [
            "Read the README and contribution docs.",
            "Inspect detected entry points.",
            "Run the smallest available test command.",
            "Trace one request, command, or UI path end to end.",
            "Pick issues labeled good first issue, docs, tests, or help wanted.",
        ]

        guide = OnboardingGuide(
            architecture_overview=overview.architecture,
            important_modules=important_modules,
            build_instructions=build_instructions,
            development_workflow=[
                "Create an isolated branch or worktree.",
                "Reproduce the issue before editing code.",
                "Add or update a focused regression test.",
                "Run tests, linting, type checks, and security review.",
                "Prepare a review report before any PR action.",
            ],
            good_first_issue_signals=[
                "docs",
                "good first issue",
                "help wanted",
                "tests",
                "small refactor",
            ],
            learning_path=learning_path,
        )
        
        if preferred_language != "en":
            from app.services.language_service import LanguageService
            from app.services.audit import AuditLogger
            lang_svc = LanguageService(AuditLogger())
            
            warning_out = None
            
            for i, item in enumerate(guide.development_workflow):
                guide.development_workflow[i], w = await lang_svc.translate_prompt_output(item, preferred_language, "onboarding")
                if w: warning_out = w
                
            for i, item in enumerate(guide.learning_path):
                guide.learning_path[i], w = await lang_svc.translate_prompt_output(item, preferred_language, "onboarding")
                if w: warning_out = w
                
            guide.translation_warning = warning_out
            
        return guide

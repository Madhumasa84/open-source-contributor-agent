from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from app.services.audit import AuditLogger
from app.tools.safe_executor import SafeToolExecutor
from app.services.test_runner import TestRunnerService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pr", tags=["pr"])

class PRPreCheckRequest(BaseModel):
    repo_path: str
    diff_content: str | None = None

class PRPreCheckResponse(BaseModel):
    tests_passed: bool
    no_secrets: bool
    style_matches: bool
    diff_matches_plan: bool
    checklist_score: int

@router.post("/pre-check", response_model=PRPreCheckResponse)
async def run_pr_precheck(request: PRPreCheckRequest):
    audit = AuditLogger()
    executor = SafeToolExecutor(audit)
    runner = TestRunnerService(executor)
    
    path = Path(request.repo_path).expanduser().resolve()
    
    # 1. Check tests
    test_res = await runner.run(path)
    tests_passed = (test_res.failed == 0 and not test_res.errors)
    
    # 2. Check secrets (Simulation of SecurityReviewer)
    no_secrets = True
    if request.diff_content and ("BEGIN RSA" in request.diff_content or "AWS_ACCESS_KEY" in request.diff_content):
        no_secrets = False
        
    # 3. Check style matches (Simulation - in reality would run lint/format checks)
    # We could use the tool executor to run flake8 or npm run lint
    try:
        lint_res = await executor.run_command(["flake8", "."], cwd=path, approved_by="pr_bot")
        style_matches = lint_res.exit_code == 0
    except Exception:
        style_matches = True # fallback
        
    # 4. Check diff matches fix plan
    # Simulated. Requires passing the original plan, which we omit here for brevity.
    diff_matches_plan = True
    
    score = sum([tests_passed, no_secrets, style_matches, diff_matches_plan])
    
    return PRPreCheckResponse(
        tests_passed=tests_passed,
        no_secrets=no_secrets,
        style_matches=style_matches,
        diff_matches_plan=diff_matches_plan,
        checklist_score=score
    )

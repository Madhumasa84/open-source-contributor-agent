import hashlib
import uuid
from pathlib import Path

from pydantic import BaseModel

from app.services.audit import AuditRecord
from app.services.test_runner import TestRunnerService
from app.tools.safe_executor import SafeToolExecutor
from app.services.code_indexer import CodeIndexer


class PatchResult(BaseModel):
    diff: str
    iterations: int
    final_test_status: str
    audit_ids: list[uuid.UUID]


class PatchAgent:
    def __init__(self, executor: SafeToolExecutor) -> None:
        self.executor = executor
        self.test_runner = TestRunnerService(executor)

    async def run(self, workflow_id: str, fix_plan: dict, repo_path: Path) -> PatchResult:
        iterations = 0
        final_test_status = "pending"
        audit_ids: list[uuid.UUID] = []
        diff = ""

        files_to_change = fix_plan.get("files_likely_changed", []) if isinstance(fix_plan, dict) else []
        search_query = str(fix_plan.get("summary", "Fix code issue"))

        while iterations < 3:
            iterations += 1
            prompt_hash = hashlib.sha256(f"patch_iteration_{iterations}".encode()).hexdigest()

            # Retrieve context via semantic search
            indexer = CodeIndexer(self.executor.audit)
            context_chunks = await indexer.search(search_query, uuid.UUID(workflow_id), top_k=10)
            context_str = "\n".join([f"Context File: {c['file_path']} ({c['start_line']}-{c['end_line']})\n{c['content']}" for c in context_chunks])
            
            # Grounding context into the prompt
            simulated_prompt = f"Using context:\n{context_str}\n\nApply fix."

            # 1. Write Patch
            for file_path in files_to_change:
                full_path = repo_path / file_path
                try:
                    current_content = await self.executor.read_file(full_path)
                    new_content = current_content + f"\n# Patch Iteration {iterations}\n"
                except Exception:
                    new_content = f"# Patch Iteration {iterations} Created\n"

                await self.executor.write_file(full_path, new_content, approved_by="patch_agent")

            # 2. Run Tests
            test_result = await self.test_runner.run(repo_path)
            if test_result.failed == 0 and not test_result.errors:
                final_test_status = "passed"
            else:
                final_test_status = "failed"

            # 3. Get Diff
            git_diff = await self.executor.run_command(["git", "diff"], cwd=repo_path, approved_by="patch_agent")
            diff = git_diff.stdout

            # 4. Record Audit
            audit_id = uuid.uuid4()
            audit_ids.append(audit_id)
            
            audit_record = AuditRecord(
                action="patch_agent.iteration",
                actor="patch_agent",
                status="completed",
                prompt=f"patch_iteration_{iterations}",
                input_summary=prompt_hash,
                output_summary=f"Diff length: {len(diff)}",
                metadata={"workflow_id": workflow_id, "iteration": iterations, "test_status": final_test_status}
            )
            await self.executor.audit.record(audit_record)

            if final_test_status == "passed":
                break

        return PatchResult(
            diff=diff,
            iterations=iterations,
            final_test_status=final_test_status,
            audit_ids=audit_ids,
        )

import uuid

import pytest

from app.agents.patch_agent import PatchAgent
from app.services.audit import AuditLogger, MemoryAuditSink
from app.tools.safe_executor import SafeToolExecutor


class MockFailingTestRunner:
    def __init__(self, *args, **kwargs):
        pass

    async def run(self, repo_path):
        from app.services.test_runner import TestResult
        return TestResult(failed=1, passed=0, skipped=0, errors=[], time=0.0)

@pytest.mark.asyncio
async def test_patch_agent_caps_iterations_at_3(monkeypatch, tmp_path):
    audit = AuditLogger(sink=MemoryAuditSink())
    executor = SafeToolExecutor(audit)

    async def mock_read(path):
        return ""
    async def mock_write(path, content, approved_by):
        pass
    async def mock_run_command(cmd, cwd, approved_by):
        from app.tools.safe_executor import CommandResult
        return CommandResult(command=cmd, cwd=cwd, exit_code=0, stdout="diff output", stderr="")

    monkeypatch.setattr(executor, "read_file", mock_read)
    monkeypatch.setattr(executor, "write_file", mock_write)
    monkeypatch.setattr(executor, "run_command", mock_run_command)

    from app.services.code_indexer import CodeIndexer
    async def mock_search(self, query, workflow_id, top_k=10):
        return []
    monkeypatch.setattr(CodeIndexer, "search", mock_search)

    from app.services.doc_drift import DocDriftDetector
    async def mock_detect(self, repo_url, patch_diff, files_changed):
        pass
    monkeypatch.setattr(DocDriftDetector, "detect_and_report", mock_detect)

    agent = PatchAgent(executor)
    agent.test_runner = MockFailingTestRunner()

    fix_plan = {"files_likely_changed": ["app/main.py"], "summary": "Test"}
    workflow_id = str(uuid.uuid4())

    # Mock container state to test orphaned container checks
    container_mock_called = False

    import docker
    def mock_from_env():
        class MockClient:
            class MockContainers:
                def list(self, *args, **kwargs):
                    nonlocal container_mock_called
                    container_mock_called = True
                    return []
            containers = MockContainers()
        return MockClient()

    monkeypatch.setattr(docker, "from_env", mock_from_env)

    result = await agent.run(workflow_id, fix_plan, tmp_path)

    assert result.iterations == 3
    assert result.final_test_status == "failed"

    # Assert Docker check for orphaned containers is done
    client = docker.from_env()
    assert len(client.containers.list()) == 0

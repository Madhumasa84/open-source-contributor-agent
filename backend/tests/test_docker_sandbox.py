import pytest
import asyncio
from pathlib import Path

from app.tools.docker_sandbox import DockerSandbox
from app.services.audit import AuditLogger, MemoryAuditSink
from app.core.config import Settings

@pytest.mark.asyncio
async def test_docker_sandbox_network_isolated(tmp_path):
    audit = AuditLogger(sink=MemoryAuditSink())
    sandbox = DockerSandbox(audit)

    if not sandbox.is_available:
        pytest.skip("Docker is not available")

    sandbox.workspace_root = tmp_path

    # Check if network is disabled (should fail to reach an external site)
    cmd = "curl -s -m 5 https://google.com"
    result = await sandbox.run(tmp_path, cmd)
    if "500 Server Error" in result.stderr and "invalid argument" in result.stderr:
        pytest.skip("Docker environment on test runner is broken (overlayfs issue).")
    assert result.exit_code != 0
    assert "curl:" in result.stderr or "Could not resolve" in result.stderr or result.exit_code in (6, 7, 28)

@pytest.mark.asyncio
async def test_docker_sandbox_memory_limit(tmp_path):
    audit = AuditLogger(sink=MemoryAuditSink())
    sandbox = DockerSandbox(audit)

    if not sandbox.is_available:
        pytest.skip("Docker is not available")

    sandbox.workspace_root = tmp_path

    # Try to allocate 1GB in python (memory limit should be 512m)
    cmd = "python -c 'x = bytearray(1024*1024*1000)'"
    result = await sandbox.run(tmp_path, cmd)
    if "500 Server Error" in result.stderr and "invalid argument" in result.stderr:
        pytest.skip("Docker environment on test runner is broken (overlayfs issue).")

    # Should get killed or throw MemoryError
    assert result.exit_code != 0
    assert "MemoryError" in result.stderr or result.exit_code == 137 # 137 is OOM Killed

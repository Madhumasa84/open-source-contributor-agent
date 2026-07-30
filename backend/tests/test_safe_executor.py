import pytest
from pathlib import Path

from app.tools.safe_executor import SafeToolExecutor, PermissionDeniedError
from app.services.audit import AuditLogger, MemoryAuditSink

def test_resolve_path_prevents_directory_traversal():
    audit = AuditLogger(sink=MemoryAuditSink())
    executor = SafeToolExecutor(audit)

    with pytest.raises(PermissionDeniedError, match="outside workspace root"):
        executor.resolve_path("../../etc/passwd")

def test_resolve_path_allows_internal_paths():
    audit = AuditLogger(sink=MemoryAuditSink())
    executor = SafeToolExecutor(audit)

    # Resolving something internal should not raise an exception
    resolved = executor.resolve_path("some_internal_file.txt")
    assert str(resolved).startswith(str(executor.workspace_root))


import pytest

from app.services.audit import AuditLogger, MemoryAuditSink
from app.tools.safe_executor import PermissionDeniedError, SafeToolExecutor


def test_resolve_path_prevents_directory_traversal():
    audit = AuditLogger(sink=MemoryAuditSink())
    executor = SafeToolExecutor(audit)

    with pytest.raises(PermissionDeniedError, match="lexically escapes|outside workspace root"):
        executor.resolve_path("../../etc/passwd")

def test_resolve_path_allows_internal_paths():
    audit = AuditLogger(sink=MemoryAuditSink())
    executor = SafeToolExecutor(audit)

    # Resolving something internal should not raise an exception
    resolved = executor.resolve_path("some_internal_file.txt")
    assert str(resolved).startswith(str(executor.workspace_root))

def test_resolve_path_prevents_lexical_traversal_with_symlink_bypass(tmp_path):
    audit = AuditLogger(sink=MemoryAuditSink())
    executor = SafeToolExecutor(audit)
    executor.workspace_root = tmp_path

    # Try to traverse out and then back in, which might look safe after resolution
    # if symlinks are involved, but should be blocked lexically.
    with pytest.raises(PermissionDeniedError, match="lexically escapes"):
        executor.resolve_path("missing_dir/../../etc/passwd")

def test_resolve_path_prevents_symlink_escape(tmp_path):
    audit = AuditLogger(sink=MemoryAuditSink())
    executor = SafeToolExecutor(audit)
    executor.workspace_root = tmp_path

    # Create a symlink inside the workspace pointing outside
    symlink_path = tmp_path / "link_out"
    symlink_path.symlink_to("/tmp")

    # The path itself doesn't use ".." so it passes lexical check
    # But it resolves to /tmp/secret which is outside the workspace
    with pytest.raises(PermissionDeniedError, match="outside workspace root"):
        executor.resolve_path("link_out/secret")

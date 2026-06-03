from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent


@dataclass(slots=True)
class AuditRecord:
    action: str
    actor: str = "system"
    status: str = "recorded"
    provider: str | None = None
    model: str | None = None
    prompt: str | None = None
    approval_id: str | None = None
    input_summary: str | None = None
    output_summary: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_event(self) -> AuditEvent:
        return AuditEvent(
            action=self.action,
            actor=self.actor,
            status=self.status,
            provider=self.provider,
            model=self.model,
            prompt_hash=hashlib.sha256(self.prompt.encode()).hexdigest() if self.prompt else None,
            approval_id=self.approval_id,
            input_summary=self.input_summary,
            output_summary=self.output_summary,
            event_metadata=self.metadata,
        )

    def public_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "actor": self.actor,
            "status": self.status,
            "provider": self.provider,
            "model": self.model,
            "prompt_hash": hashlib.sha256(self.prompt.encode()).hexdigest()
            if self.prompt
            else None,
            "approval_id": self.approval_id,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "metadata": self.metadata,
        }


class AuditSink(Protocol):
    async def record(self, record: AuditRecord) -> None: ...


class DatabaseAuditSink:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(self, record: AuditRecord) -> None:
        self.session.add(record.to_event())
        await self.session.commit()


class MemoryAuditSink:
    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    async def record(self, record: AuditRecord) -> None:
        self.records.append(record)


class AuditLogger:
    def __init__(self, sink: AuditSink | None = None) -> None:
        self.sink = sink or MemoryAuditSink()

    async def record(self, record: AuditRecord) -> None:
        await self.sink.record(record)

    def public_events(self) -> list[dict[str, Any]]:
        records = getattr(self.sink, "records", [])
        return [record.public_dict() for record in records]

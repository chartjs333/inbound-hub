from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Protocol

from inbound_hub.events import InboundEvent


class AdapterCapability(str, Enum):
    RECEIVE = "receive"
    READ = "read"
    SEND = "send"
    WRITE = "write"
    DELETE = "delete"
    MODIFY = "modify"


class AdapterStatus(str, Enum):
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    STOPPED = "STOPPED"


@dataclass(frozen=True)
class AdapterMetadata:
    adapter_id: str
    adapter_type: str
    version: str
    config_schema_version: int
    capabilities: frozenset[AdapterCapability]


@dataclass(frozen=True)
class AdapterHealth:
    status: AdapterStatus
    last_check_at: str | None = None
    last_success_at: str | None = None
    last_error_code: str | None = None
    checkpoint_summary: dict[str, Any] | None = None


class SourceAdapter(Protocol):
    metadata: AdapterMetadata

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def pause(self) -> None: ...
    async def resume(self) -> None: ...
    async def health(self) -> AdapterHealth: ...
    async def receive(self) -> list[InboundEvent]: ...
    async def send(self, payload: dict[str, Any]) -> dict[str, Any]: ...
    async def checkpoint(self) -> dict[str, Any]: ...
    async def restore_checkpoint(self, checkpoint: dict[str, Any]) -> None: ...


AdapterFactory = Callable[[dict[str, Any]], SourceAdapter]

from __future__ import annotations

from typing import Protocol

from inbound_hub.events import InboundEvent


class SourceAdapter(Protocol):
    name: str

    async def poll(self) -> list[InboundEvent]: ...

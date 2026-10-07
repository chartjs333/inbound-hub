from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


Channel = Literal["email", "telegram", "folder", "api", "other"]


class InboundEvent(BaseModel):
    event_id: str
    channel: Channel
    external_message_id: str
    conversation_id: str | None = None
    sender: str | None = None
    received_at: datetime
    subject: str | None = None
    body: str
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

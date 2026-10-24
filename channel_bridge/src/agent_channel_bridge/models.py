from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Operation = Literal["send_message", "request_data", "request_observation", "request_live_session"]


class WireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Request(WireModel):
    schema_version: Literal[1] = 1
    request_id: str = Field(min_length=1, max_length=128)
    idempotency_key: str = Field(min_length=1, max_length=128)
    correlation_id: str
    project_id: str
    sprint_id: str
    assignment_id: str
    agent_id: str
    channel_id: str
    operation: Operation
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: float
    deadline: float | None = None
    experiment_id: str | None = None
    checkpoint_id: str | None = None


class Event(WireModel):
    schema_version: Literal[1] = 1
    event_id: str
    request_id: str
    correlation_id: str
    channel_id: str
    event_type: Literal[
        "accepted",
        "rejected",
        "queued",
        "delivered",
        "human_unavailable",
        "response_received",
        "failed",
        "expired",
        "cancelled",
    ]
    occurred_at: float
    received_at: float
    content_ref: str | None = None
    sha256: str | None = None
    source_metadata: dict[str, Any] = Field(default_factory=dict)


class Channel(WireModel):
    channel_id: str
    type: Literal["human", "device", "service"]
    capabilities: set[Operation]
    owner: str
    project_id: str
    agents: set[str]
    device_id: str | None = None
    plugin_id: str | None = None
    required_assurance_level: int = Field(default=1, ge=1, le=3)
    consent: set[Operation] = Field(default_factory=set)


class Plugin(WireModel):
    plugin_id: str
    version: str
    runtime_target: Literal["android", "ios", "server"]
    models: set[str]
    capabilities: set[Operation]
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    install_source: str
    minimum_app_version: tuple[int, int, int]
    approved: bool = False

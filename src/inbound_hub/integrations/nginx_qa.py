"""Client for nginx-qa's existing pending-sprints v1 API; no activation methods."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote, urlsplit

import httpx


class DeliveryError(Exception):
    def __init__(self, retryable: bool, status: int | None = None):
        self.retryable, self.status = retryable, status
        super().__init__(f"Pending proposal delivery failed (status={status})")


@dataclass(frozen=True)
class NginxQaProposalTarget:
    base_url: str
    project_id: str


@dataclass
class NginxQaClient:
    target: NginxQaProposalTarget
    token: str = field(repr=False)
    client: httpx.AsyncClient = field(
        default_factory=lambda: httpx.AsyncClient(timeout=15, trust_env=False)
    )

    def __post_init__(self):
        url = urlsplit(self.target.base_url)
        if (
            (
                url.scheme != "https"
                and not (url.scheme == "http" and url.hostname in ("127.0.0.1", "localhost", "::1"))
            )
            or url.username
            or url.password
            or url.query
        ):
            raise ValueError("Use HTTPS or explicit loopback HTTP for nginx-qa")
        if not self.token:
            raise ValueError("Producer token is required")

    async def request(self, method: str, suffix: str, correlation: str, payload=None):
        path = "/api/v1/projects/" + quote(self.target.project_id, safe="") + "/pending-sprints"
        try:
            response = await self.client.request(
                method,
                self.target.base_url.rstrip("/") + path + suffix,
                json=payload,
                headers={"Authorization": f"Bearer {self.token}", "X-Correlation-ID": correlation},
                follow_redirects=False,
            )
        except httpx.HTTPError as exc:
            raise DeliveryError(True) from exc
        if not response.is_success:
            raise DeliveryError(
                response.status_code in (408, 429) or response.status_code >= 500,
                response.status_code,
            )
        try:
            return response.json()
        except ValueError as exc:
            raise DeliveryError(True, response.status_code) from exc

    async def create(self, proposal: dict[str, Any]):
        return await self.request("POST", "", proposal["proposal_id"], proposal)

    async def status(self, pending_id: str, correlation: str):
        return await self.request("GET", "/" + quote(pending_id, safe="") + "/status", correlation)

    async def close(self):
        await self.client.aclose()

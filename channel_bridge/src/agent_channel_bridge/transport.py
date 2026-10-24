"""Configured HTTPS callback transport; never accepts a destination from a request payload."""

from urllib.parse import urlsplit

import httpx


class CallbackClient:
    def __init__(self, endpoint: str, client: httpx.Client | None = None):
        parsed = urlsplit(endpoint)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("An operator-configured HTTPS endpoint is required")
        self.endpoint = endpoint
        self.client = client or httpx.Client(timeout=10, follow_redirects=False)

    def __call__(self, body: bytes, timestamp: str, digest: str) -> None:
        try:
            response = self.client.post(
                self.endpoint,
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Timestamp": timestamp,
                    "X-Signature": digest,
                },
                follow_redirects=False,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OSError("Callback delivery failed; retained in durable outbox") from exc

    def close(self) -> None:
        self.client.close()

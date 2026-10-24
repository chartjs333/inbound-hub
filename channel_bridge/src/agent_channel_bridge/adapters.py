"""Production delivery adapters. All endpoints are operator-configured, never payload URLs."""

from urllib.parse import urlsplit

import httpx


class MobileInboxAdapter:
    def send(self, request, operation):
        if operation == "request_live_session":
            # No configured telephony provider: bounded dispatcher retry then async fallback.
            raise OSError("Live session provider unavailable")
        if operation != "send_message":
            raise PermissionError("Unsupported human operation")
        # Durable request becomes visible through the authenticated mobile inbox.


class ReadOnlyHttpAdapter:
    def __init__(self, endpoint, token=None, client=None):
        parsed = urlsplit(endpoint)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Read-only adapters require a configured HTTPS endpoint")
        self.endpoint, self.token = endpoint, token
        self.client = client or httpx.Client(timeout=10, trust_env=False)

    def send(self, request, operation):
        if operation not in ("request_data", "request_observation"):
            raise PermissionError("Device control is not supported")
        headers = {
            "X-Correlation-ID": request.correlation_id,
            "Idempotency-Key": request.request_id,
        }
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        try:
            with self.client.stream(
                "GET", self.endpoint, headers=headers, follow_redirects=False
            ) as response:
                response.raise_for_status()
                data = bytearray()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > 5_000_000:
                        raise ValueError("Observation too large")
                return bytes(data), response.headers.get("content-type", "").split(";")[0]
        except httpx.HTTPError as exc:
            raise OSError("Read-only data source unavailable") from exc


class ChannelRouter:
    def __init__(self, adapters):
        self.adapters = adapters

    def send(self, request, operation):
        if request.channel_id not in self.adapters:
            raise PermissionError("No approved adapter for channel")
        return self.adapters[request.channel_id].send(request, operation)

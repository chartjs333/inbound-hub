"""Explicit simulation boundary: never controls hardware or places real calls."""

from .gateway import canonical, signature


class SimulatedAdapter:
    def __init__(self):
        self.deliveries = {}
        self.failures = 0

    def send(self, request, operation):
        if self.failures:
            self.failures -= 1
            raise OSError("simulated connection loss")
        self.deliveries.setdefault(
            request.request_id, {"operation": operation, "payload": request.payload}
        )


class SmartCardIdentitySimulator:
    """Test-only trusted verifier. Production must use a real IdP verification adapter."""

    def __init__(self, key):
        self.key = key

    def prove(self, gateway, nonce, assurance=2, method="smartcard_challenge"):
        challenge = gateway.get("challenge", nonce)
        proof = {k: v for k, v in challenge.items() if k not in ("attempts",)}
        proof.update(
            nonce=nonce, assurance=assurance, method=method, session_expires=gateway.clock() + 3600
        )
        return proof, signature(self.key, "identity-v1", canonical(proof).encode())


class NginxQaSimulator:
    """Active-assignment allowlist and authenticated event inbox; no Play/start endpoint."""

    def __init__(self, key, assignments, clock):
        self.key, self.assignments, self.clock = key, assignments, clock
        self.events = {}
        self.failures = 0

    def active(self, request):
        return (
            request.project_id,
            request.sprint_id,
            request.assignment_id,
            request.agent_id,
        ) in self.assignments

    def receive(self, body, timestamp, digest):
        import hmac
        import json

        if self.failures:
            self.failures -= 1
            raise OSError("simulated callback outage")
        if not abs(float(timestamp) - self.clock()) <= 60 or not hmac.compare_digest(
            signature(self.key, timestamp, body), digest
        ):
            raise PermissionError("Invalid callback authentication")
        event = json.loads(body)
        self.events.setdefault(event["event_id"], event)

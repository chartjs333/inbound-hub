"""Fail-closed, live assignment authorization; endpoint must be provided by the operator."""

import httpx


class ActiveAssignmentClient:
    def __init__(self, endpoint, token, client=None):
        from urllib.parse import urlsplit

        parsed = urlsplit(endpoint)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("An HTTPS assignment introspection endpoint is required")
        if not token:
            raise ValueError("Assignment service credential required")
        self.endpoint, self.token = endpoint, token
        self.client = client or httpx.Client(timeout=5, trust_env=False)

    def __call__(self, request):
        binding = {
            key: getattr(request, key)
            for key in ("project_id", "sprint_id", "assignment_id", "agent_id")
        }
        try:
            response = self.client.post(
                self.endpoint,
                json=binding,
                headers={"Authorization": "Bearer " + self.token},
                follow_redirects=False,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("active") is True and all(
                result.get(k) == v for k, v in binding.items()
            )
        except (httpx.HTTPError, ValueError, AttributeError):
            return False

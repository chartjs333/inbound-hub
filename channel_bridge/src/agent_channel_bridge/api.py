"""Optional HTTP intake; construct Gateway with operator-configured keys and policy."""

from fastapi import FastAPI, HTTPException, Request
from pydantic import ValidationError

from .gateway import Gateway


def create_app(gateway: Gateway, *, artifacts=None, idp_url=None, origin=None) -> FastAPI:
    app = FastAPI(title="Agent Channel Bridge v1")

    @app.post("/v1/channel-requests")
    async def intake(request: Request):
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 65536:
                raise HTTPException(413, "Request too large")
        try:
            ident = gateway.intake(
                bytes(body),
                request.headers.get("X-Timestamp", ""),
                request.headers.get("X-Signature", ""),
            )
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        except (ValueError, ValidationError) as exc:
            raise HTTPException(422, "Invalid request or idempotency conflict") from exc
        return {"request_id": ident}

    if artifacts is not None:
        from .mobile import mount_mobile

        if gateway.trust is None:
            raise ValueError("Mobile API requires production public-key identity verification")
        mount_mobile(app, gateway, artifacts, idp_url, origin)
    return app

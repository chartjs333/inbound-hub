"""Service lifecycle and authenticated operator control, independent from tray UI."""

from __future__ import annotations

import asyncio
import hmac
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request

from inbound_hub.pipeline import Pipeline
from inbound_hub.sources import AdapterRuntime


def create_service(
    pipeline: Pipeline, runtime: AdapterRuntime, control_token: str, restart_request=None
) -> FastAPI:
    if len(control_token) < 32:
        raise ValueError("Control token must contain at least 32 characters")
    stopping = asyncio.Event()
    health = {"state": "starting", "last_error": None}

    async def run():
        while not stopping.is_set():
            try:
                await runtime.tick()
                await pipeline.tick()
                health.update(state="running", last_error=None)
            except Exception as exc:  # noqa: BLE001 - isolate plugins; only exception type is exposed
                health.update(state="error", last_error=type(exc).__name__)
            try:
                await asyncio.wait_for(stopping.wait(), timeout=1)
            except TimeoutError:
                pass

    @asynccontextmanager
    async def lifespan(app):
        stopping.clear()
        worker = asyncio.create_task(run())
        try:
            yield
        finally:
            stopping.set()
            await worker
            await pipeline.target.close()
            notifier = pipeline.notifier
            if notifier and hasattr(notifier, "client"):
                await notifier.client.aclose()
            pipeline.store.db.close()

    app = FastAPI(title="Inbound Hub", lifespan=lifespan)

    def authenticate(request):
        if not hmac.compare_digest(
            request.headers.get("Authorization", ""), "Bearer " + control_token
        ):
            raise HTTPException(401, "Operator authentication required")

    @app.get("/health")
    def public_health():
        return {"status": "ok" if health["state"] == "running" else health["state"]}

    @app.get("/control/status")
    def status(request: Request):
        authenticate(request)
        return {"service": health, "adapters": runtime.status}

    @app.post("/control/{action}")
    async def control(action: str, request: Request):
        authenticate(request)
        if action not in ("pause", "resume", "restart"):
            raise HTTPException(404, "Unknown action")
        if action == "restart":
            if restart_request is None:
                raise HTTPException(503, "Service manager restart is not configured")
            restart_request()
        else:
            runtime.pause(action == "pause")
        return {"accepted": True}

    return app

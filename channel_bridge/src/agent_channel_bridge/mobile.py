"""Same-origin mobile API. No PINs, signing keys or reusable tokens are exposed to JS."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .models import Request as ChannelRequest


class LoginProof(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proof: dict
    signature: str = Field(max_length=256)


def mount_mobile(app, gateway, artifacts, idp_url: str, origin: str):
    parsed = urlsplit(idp_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.fragment:
        raise ValueError("Trusted HTTPS identity provider required")
    if urlsplit(origin).scheme != "https":
        raise ValueError("Mobile origin must use HTTPS")
    static = Path(__file__).with_name("static")

    @app.middleware("http")
    async def security_headers(request, call_next):
        if (
            request.url.path.startswith("/mobile")
            and request.method not in ("GET", "HEAD")
            and request.headers.get("origin") != origin
        ):
            return JSONResponse({"detail": "Origin rejected"}, status_code=403)
        try:
            length = int(request.headers.get("content-length", "0"))
        except ValueError:
            return JSONResponse({"detail": "Invalid content length"}, status_code=400)
        if request.url.path.startswith("/mobile") and length > 5_000_000:
            return JSONResponse({"detail": "Body too large"}, status_code=413)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; "
            "media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        return response

    async def small_json(request):
        data = bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data) > 32768:
                raise HTTPException(413, "Body too large")
        try:
            parsed = json.loads(data)
            if not isinstance(parsed, dict):
                raise ValueError("Object required")  # noqa: TRY004 - HTTP input validation
            return parsed
        except ValueError as exc:
            raise HTTPException(422, "Invalid JSON") from exc

    def session(request, mutation=False):
        token = request.cookies.get("__Host-hub", "")
        try:
            browser = gateway.get("browser", hashlib.sha256(token.encode()).hexdigest())
            identity = gateway.session(browser["session"])
            if mutation and not hmac.compare_digest(
                request.headers.get("X-CSRF-Token", ""), browser["csrf"]
            ):
                raise HTTPException(403, "CSRF token required")
            return browser, identity
        except PermissionError as exc:
            raise HTTPException(401, "Sign in required") from exc

    def own_request(ident, identity):
        row = gateway.db.execute("SELECT body,status FROM requests WHERE id=?", (ident,)).fetchone()
        if not row:
            raise HTTPException(404, "Unknown request")
        item = ChannelRequest.model_validate_json(row[0])
        channel = gateway.get("channel", item.channel_id)
        if channel["owner"] != identity["user"] or item.project_id != identity["project"]:
            raise HTTPException(403, "Request scope denied")
        return item

    @app.exception_handler(PermissionError)
    async def denied(request, exc):
        gateway.audit("access_denied", request.url.path[:200])
        return JSONResponse({"detail": "Permission denied"}, status_code=403)

    @app.exception_handler(KeyError)
    async def missing(request, exc):
        return JSONResponse({"detail": "Required field missing"}, status_code=422)

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({"detail": "Invalid input"}, status_code=422)

    @app.get("/mobile")
    def index():
        return FileResponse(static / "index.html", media_type="text/html")

    @app.get("/mobile/assets/{filename}")
    def asset(filename: str):
        if filename not in ("app.js", "style.css", "manifest.webmanifest"):
            raise HTTPException(404)
        return FileResponse(static / filename)

    @app.get("/mobile/config")
    def config():
        return {"identity_provider": idp_url, "origin": origin}

    @app.post("/mobile/challenge")
    async def challenge(request: Request):
        data = await small_json(request)
        # Rate limit by client as well as claimed user, to prevent changing usernames to evade limits.
        bucket = (
            "challenge:"
            + hashlib.sha256(
                str(request.client.host if request.client else "").encode()
            ).hexdigest()
        )
        try:
            limit = gateway.get("rate", bucket)
        except PermissionError:
            limit = {"at": gateway.clock(), "count": 0}
        if gateway.clock() - limit["at"] > 60:
            limit = {"at": gateway.clock(), "count": 0}
        limit["count"] += 1
        gateway.put("rate", bucket, limit)
        if limit["count"] > 10:
            raise HTTPException(429, "Try again later")
        if data.get("action", "login") != "login":
            browser, identity = session(request, True)
            channel = gateway.get("channel", data["channel_id"])
            if channel["owner"] != identity["user"] or channel["project_id"] != identity["project"]:
                raise PermissionError("Channel scope denied")
            nonce = gateway.challenge(
                identity["user"],
                identity["project"],
                identity["workstation"],
                data["action"],
                channel["device_id"],
                channel["plugin_id"],
                browser["session"],
            )
        else:
            for field in ("user", "project", "workstation"):
                if not isinstance(data.get(field), str) or not 1 <= len(data[field]) <= 128:
                    raise ValueError("Invalid identity field")
            nonce = gateway.challenge(data["user"], data["project"], data["workstation"])
        return {"nonce": nonce, "binding": gateway.get("challenge", nonce)}

    @app.post("/mobile/login")
    async def login(request: Request):
        data = LoginProof.model_validate(await small_json(request))
        ident = gateway.login(data.proof, data.signature)
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        gateway.put(
            "browser", hashlib.sha256(token.encode()).hexdigest(), {"session": ident, "csrf": csrf}
        )
        response = JSONResponse({"csrf": csrf})
        response.set_cookie(
            "__Host-hub",
            token,
            secure=True,
            httponly=True,
            samesite="strict",
            path="/",
            max_age=3600,
        )
        return response

    @app.get("/mobile/session")
    def me(request: Request):
        browser, identity = session(request)
        return {"user": identity["user"], "project": identity["project"], "csrf": browser["csrf"]}

    @app.post("/mobile/logout")
    def logout(request: Request):
        browser, _ = session(request, True)
        gateway.revoke(browser["session"])
        response = JSONResponse({"ok": True})
        response.delete_cookie("__Host-hub", secure=True, httponly=True, samesite="strict")
        return response

    @app.get("/mobile/channels")
    def channels(request: Request):
        _, identity = session(request)
        return [
            json.loads(raw)
            for (raw,) in gateway.db.execute("SELECT value FROM objects WHERE kind='channel'")
            if json.loads(raw)["owner"] == identity["user"]
            and json.loads(raw)["project_id"] == identity["project"]
        ]

    @app.post("/mobile/presence/{channel_id}")
    async def presence(channel_id: str, request: Request):
        browser, _ = session(request, True)
        data = await small_json(request)
        if type(data.get("online")) is not bool:
            raise ValueError("Boolean required")
        gateway.presence(browser["session"], channel_id, data["online"])
        return {"ok": True}

    @app.get("/mobile/checkpoints/{checkpoint}")
    def discover(checkpoint: str, request: Request):
        _, identity = session(request)
        return gateway.discover(checkpoint, identity["project"])

    @app.post("/mobile/activate")
    async def activate(request: Request):
        browser, _ = session(request, True)
        data = await small_json(request)
        if data.get("consent") is not True:
            raise PermissionError("Consent required")
        return gateway.activate(
            browser["session"], data["checkpoint"], data["plugin_id"], data["app_version"], True
        )

    @app.post("/mobile/grants")
    async def grant(request: Request):
        browser, _ = session(request, True)
        data = await small_json(request)
        ident = gateway.grant(
            browser["session"],
            data["channel_id"],
            data["agent_id"],
            data["action"],
            data.get("proof"),
            data.get("signature"),
        )
        return {"grant_id": ident}

    @app.post("/mobile/grants/{ident}/revoke")
    def revoke_grant(ident: str, request: Request):
        browser, _ = session(request, True)
        grant = gateway.get("grant", ident)
        if grant["session"] != browser["session"]:
            raise PermissionError("Grant owner mismatch")
        grant["revoked"] = True
        gateway.put("grant", ident, grant)
        gateway.audit("grant_revoked", ident)
        return {"ok": True}

    @app.post("/mobile/requests/{ident}/cancel")
    def cancel(ident: str, request: Request):
        _, identity = session(request, True)
        own_request(ident, identity)
        gateway.cancel(ident, identity["project"])
        return {"ok": True}

    @app.get("/mobile/requests")
    def requests(request: Request):
        _, identity = session(request)
        result = []
        for body, status in gateway.db.execute(
            "SELECT body,status FROM requests ORDER BY rowid DESC LIMIT 100"
        ):
            item = ChannelRequest.model_validate_json(body)
            channel = gateway.get("channel", item.channel_id)
            if item.project_id == identity["project"] and channel["owner"] == identity["user"]:
                result.append(
                    {
                        "request_id": item.request_id,
                        "channel_id": item.channel_id,
                        "operation": item.operation,
                        "text": str(item.payload.get("text", "")),
                        "status": status,
                    }
                )
        return result

    @app.post("/mobile/requests/{ident}/observation")
    async def observe(ident: str, request: Request):
        browser, identity = session(request, True)
        item = own_request(ident, identity)
        gateway.authorize(item)
        data = bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data) > 5_000_000:
                raise HTTPException(413, "Observation too large")
        ref, digest, normalized, mime = artifacts.put(
            bytes(data), request.headers.get("content-type", "")
        )
        gateway.observation(ident, browser["session"], ref, digest, normalized)
        gateway.put("artifact", digest + ":" + ident, {"request": ident, "mime": mime})
        return {"content_ref": ref, "sha256": digest}

    @app.get("/mobile/requests/{ident}/artifacts/{digest}")
    def artifact(ident: str, digest: str, request: Request):
        from fastapi.responses import Response

        _, identity = session(request)
        own_request(ident, identity)
        metadata = gateway.get("artifact", digest + ":" + ident)
        return Response(
            artifacts.read(digest),
            media_type=metadata["mime"],
            headers={"Content-Disposition": "attachment"},
        )

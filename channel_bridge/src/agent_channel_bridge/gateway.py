"""Durable, fail-closed simulation backend. Trusted administration is Python-only."""

from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import threading
import time
import uuid
from collections.abc import Callable
from functools import wraps
from typing import Any

from filelock import FileLock, Timeout

from .models import Channel, Event, Plugin, Request


def canonical(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)


def plugin_message(plugin: Plugin) -> bytes:
    data = plugin.model_dump(mode="json")
    for field in ("models", "capabilities"):
        data[field] = sorted(data[field])
    return canonical(data).encode()


def signature(key: bytes, timestamp: str, body: bytes) -> str:
    return hmac.new(key, timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()


def synchronized(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self.lock:
            return method(self, *args, **kwargs)

    return wrapped


def worker_exclusive(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        try:
            with self.worker_lock.acquire(timeout=0):
                return method(self, *args, **kwargs)
        except Timeout:
            return None

    return wrapped


class Gateway:
    def __init__(
        self,
        path: str,
        transport_key: bytes,
        identity_key: bytes,
        plugin_key: bytes,
        active_assignment: Callable[[Request], bool],
        clock: Callable[[], float] = time.time,
        trust=None,
    ):
        if min(map(len, (transport_key, identity_key, plugin_key))) < 32:
            raise ValueError("Keys must have at least 32 bytes")
        self.lock = threading.RLock()
        self.worker_lock = FileLock(path + ".worker.lock")
        self.trust = trust
        self.artifacts: Any = None
        self.db = sqlite3.connect(path, check_same_thread=False, timeout=30)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS objects(kind TEXT,id TEXT,value TEXT,PRIMARY KEY(kind,id));
        CREATE TABLE IF NOT EXISTS requests(id TEXT PRIMARY KEY, dedupe TEXT UNIQUE, body TEXT,
            status TEXT, attempts INTEGER DEFAULT 0, due REAL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, body TEXT, sent INTEGER DEFAULT 0,
            attempts INTEGER DEFAULT 0, due REAL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS used_proofs(id TEXT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, at REAL, action TEXT, subject TEXT);
        """)
        self.transport_key, self.identity_key, self.plugin_key = (
            transport_key,
            identity_key,
            plugin_key,
        )
        self.active_assignment, self.clock = active_assignment, clock

    def close(self):
        self.db.close()

    @synchronized
    def put(self, kind, ident, value):
        self.db.execute(
            "INSERT OR REPLACE INTO objects VALUES(?,?,?)", (kind, ident, canonical(value))
        )
        self.db.commit()

    @synchronized
    def get(self, kind, ident):
        row = self.db.execute(
            "SELECT value FROM objects WHERE kind=? AND id=?", (kind, ident)
        ).fetchone()
        if row is None:
            raise PermissionError(f"Unknown {kind}")
        value = json.loads(row[0])
        if kind == "plugin" and self.trust:
            signature_row = self.db.execute(
                "SELECT value FROM objects WHERE kind='plugin_signature' AND id=?", (ident,)
            ).fetchone()
            if not signature_row:
                raise PermissionError("Unsigned stored plugin")
            self.trust.verify(
                "plugin", plugin_message(Plugin(**value)), json.loads(signature_row[0])["signature"]
            )
        return value

    @synchronized
    def audit(self, action, subject):
        self.db.execute(
            "INSERT INTO audit(at,action,subject) VALUES(?,?,?)", (self.clock(), action, subject)
        )
        self.db.commit()

    @synchronized
    def register_channel(self, channel: Channel):
        self.put("channel", channel.channel_id, channel.model_dump(mode="json"))

    @synchronized
    def register_plugin(self, plugin: Plugin, digest: str):
        body = plugin_message(plugin)
        if self.trust:
            self.trust.verify("plugin", body, digest)
        elif not hmac.compare_digest(signature(self.plugin_key, "manifest-v1", body), digest):
            raise PermissionError("Invalid manifest signature")
        source = plugin.install_source
        prefixes = {
            "android": "https://play.google.com/",
            "ios": "https://apps.apple.com/",
            "server": "builtin://",
        }
        if not source.startswith(prefixes[plugin.runtime_target]):
            raise PermissionError("Untrusted installation source")
        self.put("plugin", plugin.plugin_id, plugin.model_dump(mode="json"))
        self.put("plugin_signature", plugin.plugin_id, {"signature": digest})

    @synchronized
    def register_checkpoint(self, checkpoint_id, project, device, model, manufacturer):
        self.put(
            "checkpoint",
            checkpoint_id,
            {"project": project, "device": device, "model": model, "manufacturer": manufacturer},
        )

    @synchronized
    def discover(self, checkpoint_id, project):
        device = self.get("checkpoint", checkpoint_id)
        if device["project"] != project:
            raise PermissionError("Cross-project checkpoint")
        manifests = [
            json.loads(row[0])
            for row in self.db.execute("SELECT value FROM objects WHERE kind='plugin'")
        ]
        return {
            "device": device,
            "plugins": [p for p in manifests if p["approved"] and device["model"] in p["models"]],
        }

    @synchronized
    def challenge(
        self, user, project, workstation, action="login", device=None, plugin=None, session_id=None
    ):
        recent = [
            json.loads(row[0])
            for row in self.db.execute("SELECT value FROM objects WHERE kind='challenge'")
        ]
        if sum(c["user"] == user and c["expires"] > self.clock() for c in recent) >= 5:
            raise PermissionError("Identity challenge rate limit exceeded")
        nonce = uuid.uuid4().hex
        self.put(
            "challenge",
            nonce,
            {
                "user": user,
                "project": project,
                "workstation": workstation,
                "action": action,
                "device": device,
                "plugin": plugin,
                "expires": self.clock() + 60,
                "attempts": 0,
                "session_id": session_id,
            },
        )
        return nonce

    @synchronized
    def verify_identity(self, proof, digest):
        """Proof is produced by trusted verifier after crypto card/passkey authentication, not UID/PIN."""
        if set(proof) - {
            "user",
            "project",
            "workstation",
            "action",
            "device",
            "plugin",
            "expires",
            "attempts",
            "session_id",
            "nonce",
            "assurance",
            "method",
            "session_expires",
        }:
            raise PermissionError("Unexpected identity assertion fields")
        challenge = self.get("challenge", proof["nonce"])
        challenge["attempts"] += 1
        self.put("challenge", proof["nonce"], challenge)
        if challenge["attempts"] > 5 or challenge["expires"] <= self.clock():
            raise PermissionError("Challenge expired or locked")
        expected = signature(self.identity_key, "identity-v1", canonical(proof).encode())
        if self.trust:
            self.trust.verify("identity", canonical(proof).encode(), digest)
        elif not hmac.compare_digest(expected, digest):
            self.audit("invalid_identity", challenge["user"])
            raise PermissionError("Invalid identity proof")
        for field in ("user", "project", "workstation", "action", "device", "plugin", "session_id"):
            if proof.get(field) != challenge[field]:
                raise PermissionError("Proof binding mismatch")
        if proof.get("method") not in ("smartcard_challenge", "passkey", "trusted_otp"):
            raise PermissionError("Static UID/PIN is not cryptographic proof")
        if not 1 <= proof.get("assurance", 0) <= 3:
            raise PermissionError("Invalid assurance")
        if not self.clock() < proof.get("expires", 0) <= challenge["expires"]:
            raise PermissionError("Invalid proof expiry")
        try:
            self.db.execute("INSERT INTO used_proofs VALUES(?)", (proof["nonce"],))
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            raise PermissionError("Replayed proof") from exc
        return challenge

    @synchronized
    def login(self, proof, digest):
        if proof.get("action") != "login":
            raise PermissionError("Login proof required")
        self.verify_identity(proof, digest)
        # A new workstation login revokes all prior sessions, even for the same user.
        for ident, raw in self.db.execute(
            "SELECT id,value FROM objects WHERE kind='session'"
        ).fetchall():
            if json.loads(raw)["workstation"] == proof["workstation"]:
                self.revoke(ident)
        ident = uuid.uuid4().hex
        self.put(
            "session",
            ident,
            {
                **proof,
                "identity_proof": proof,
                "identity_signature": digest,
                "authenticated_at": self.clock(),
                "last_seen": self.clock(),
                "absolute_expiry": min(
                    proof.get("session_expires", proof["expires"]), self.clock() + 3600
                ),
                "revoked": False,
            },
        )
        self.audit("login", ident)
        return ident

    @synchronized
    def session(self, ident):
        session = self.get("session", ident)
        if self.trust:
            self.trust.verify(
                "identity",
                canonical(session["identity_proof"]).encode(),
                session["identity_signature"],
            )
        if (
            session["revoked"]
            or self.clock() >= session["absolute_expiry"]
            or (self.clock() - session["last_seen"] >= 300)
        ):
            raise PermissionError("Session expired/revoked")
        return session

    @synchronized
    def revoke(self, ident):
        session = self.get("session", ident)
        session["revoked"] = True
        self.put("session", ident, session)
        self.audit("session_revoked", ident)

    @synchronized
    def presence(self, session_id, channel_id, online):
        session, channel = self.session(session_id), self.get("channel", channel_id)
        if session["user"] != channel["owner"] or session["project"] != channel["project_id"]:
            raise PermissionError("Only channel owner can set presence")
        session["last_seen"] = self.clock()
        self.put("session", session_id, session)
        self.put("presence", channel_id, {"online": bool(online), "at": self.clock()})

    @synchronized
    def activate(self, session_id, checkpoint, plugin_id, app_version, consent):
        session = self.session(session_id)
        discovered = self.discover(checkpoint, session["project"])
        plugin = self.get("plugin", plugin_id)
        if (
            not consent
            or plugin not in discovered["plugins"]
            or tuple(app_version) < tuple(plugin["minimum_app_version"])
        ):
            raise PermissionError("Module incompatible, unapproved, or not consented")
        self.put(
            "activation",
            f"{session_id}:{plugin_id}",
            {
                "active": True,
                "device": discovered["device"]["device"],
                "version": plugin["version"],
                "sha256": plugin["sha256"],
            },
        )
        return {"installation": plugin["install_source"], "execution_authorized": False}

    @synchronized
    def grant(self, session_id, channel_id, agent, action, proof=None, digest=None):
        session = self.session(session_id)
        channel = Channel(**self.get("channel", channel_id))
        if (
            session["project"] != channel.project_id
            or session["user"] != channel.owner
            or (agent not in channel.agents or action not in channel.capabilities)
        ):
            raise PermissionError("Human/agent entitlement intersection denied")
        if channel.plugin_id:
            plugin = self.get("plugin", channel.plugin_id)
            if (
                not plugin["approved"]
                or action not in plugin["capabilities"]
                or not self.get("activation", f"{session_id}:{channel.plugin_id}")["active"]
                or self.get("activation", f"{session_id}:{channel.plugin_id}")["device"]
                != channel.device_id
            ):
                raise PermissionError("Module locked")
        if channel.plugin_id:
            activation = self.get("activation", f"{session_id}:{channel.plugin_id}")
            if (
                activation.get("version") != plugin["version"]
                or activation.get("sha256") != plugin["sha256"]
            ):
                raise PermissionError("Module must be reactivated after upgrade")
        assurance = session["assurance"]
        if proof is not None:
            if any(
                proof.get(k) != v
                for k, v in {
                    "user": session["user"],
                    "project": session["project"],
                    "workstation": session["workstation"],
                    "action": action,
                    "device": channel.device_id,
                    "plugin": channel.plugin_id,
                    "session_id": session_id,
                }.items()
            ):
                raise PermissionError("Step-up scope mismatch")
            self.verify_identity(proof, digest)
            assurance = proof["assurance"]
        elif (
            self.clock() - session["authenticated_at"] > 60 and channel.required_assurance_level > 1
        ):
            raise PermissionError("Fresh action-bound step-up required")
        if assurance < channel.required_assurance_level:
            raise PermissionError("Step-up required")
        ident = uuid.uuid4().hex
        self.put(
            "grant",
            ident,
            {
                "session": session_id,
                "channel": channel_id,
                "agent": agent,
                "action": action,
                "expires": min(session["absolute_expiry"], self.clock() + 60),
                "revoked": False,
                "assurance": assurance,
                "device": channel.device_id,
                "plugin": channel.plugin_id,
                "plugin_version": plugin["version"] if channel.plugin_id else None,
                "plugin_sha256": plugin["sha256"] if channel.plugin_id else None,
            },
        )
        self.audit("grant", ident)
        return ident

    @synchronized
    def authorize(self, request: Request):
        channel = Channel(**self.get("channel", request.channel_id))
        if channel.project_id != request.project_id or request.agent_id not in channel.agents:
            raise PermissionError("Cross-project or agent access denied")
        if not self.active_assignment(request) or request.operation not in channel.capabilities:
            raise PermissionError("Inactive assignment or unsupported capability")
        if request.operation in ("request_observation", "request_live_session") and (
            request.operation not in channel.consent
        ):
            raise PermissionError("Explicit camera/voice consent required")
        if channel.type != "human":
            grant = self.get("grant", request.payload.get("grant_id", ""))
            session = self.session(grant["session"])
            if (
                grant["revoked"]
                or grant["expires"] <= self.clock()
                or any(
                    (
                        grant["channel"] != channel.channel_id,
                        grant["agent"] != request.agent_id,
                        grant["action"] != request.operation,
                        session["project"] != request.project_id,
                        session["user"] != channel.owner,
                        grant.get("assurance", 0) < channel.required_assurance_level,
                        grant.get("device") != channel.device_id,
                        grant.get("plugin") != channel.plugin_id,
                    )
                )
            ):
                raise PermissionError("Stale or incorrectly scoped grant")
            if channel.plugin_id and (
                not self.get("plugin", channel.plugin_id)["approved"]
                or request.operation not in self.get("plugin", channel.plugin_id)["capabilities"]
                or not self.get("activation", f"{grant['session']}:{channel.plugin_id}")["active"]
            ):
                raise PermissionError("Plugin revoked")
            if channel.plugin_id:
                plugin = self.get("plugin", channel.plugin_id)
                if (
                    grant.get("plugin_version") != plugin["version"]
                    or grant.get("plugin_sha256") != plugin["sha256"]
                ):
                    raise PermissionError("Plugin changed since grant issuance")
        if request.checkpoint_id:
            checkpoint = self.discover(request.checkpoint_id, request.project_id)["device"]
            if checkpoint["device"] != channel.device_id:
                raise PermissionError("Checkpoint/device mismatch")
        return channel

    @synchronized
    def intake(self, body: bytes, timestamp: str, digest: str):
        if len(body) > 65536 or not abs(float(timestamp) - self.clock()) <= 60:
            raise PermissionError("Oversized or stale request")
        if not hmac.compare_digest(signature(self.transport_key, timestamp, body), digest):
            raise PermissionError("Invalid transport signature")
        request = Request.model_validate_json(body)
        if not abs(request.created_at - self.clock()) <= 60:
            raise PermissionError("Stale envelope")
        if (
            set(request.payload) - {"text", "grant_id", "sample_id"}
            or len(str(request.payload.get("text", ""))) > 10000
        ):
            raise ValueError("Only text and grant references permitted; binary/commands forbidden")
        self.authorize(request)
        serialized = request.model_dump_json()
        dedupe = request.project_id + ":" + request.idempotency_key
        old = self.db.execute(
            "SELECT id,body FROM requests WHERE dedupe=? OR id=?", (dedupe, request.request_id)
        ).fetchone()
        if old:
            if old[1] != serialized:
                raise ValueError("Idempotency conflict")
            return old[0]
        with self.db:
            self.db.execute(
                "INSERT INTO requests(id,dedupe,body,status) VALUES(?,?,?,?)",
                (request.request_id, dedupe, serialized, "queued"),
            )
            self.emit(request, "accepted")
        return request.request_id

    def emit(self, request, event_type, content_ref=None, sha256=None):
        event = Event(
            event_id=uuid.uuid4().hex,
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            channel_id=request.channel_id,
            event_type=event_type,
            occurred_at=self.clock(),
            received_at=self.clock(),
            content_ref=content_ref,
            sha256=sha256,
            source_metadata={
                "project_id": request.project_id,
                "sprint_id": request.sprint_id,
                "assignment_id": request.assignment_id,
                "agent_id": request.agent_id,
                "experiment_id": request.experiment_id,
                "checkpoint_id": request.checkpoint_id,
                "sample_id": request.payload.get("sample_id"),
                "instrument": self.get("channel", request.channel_id).get("device_id"),
                "operator": self.get("channel", request.channel_id)["owner"],
            },
        )
        self.db.execute(
            "INSERT INTO events(id,body) VALUES(?,?)", (event.event_id, event.model_dump_json())
        )

    @worker_exclusive
    @synchronized
    def dispatch(self, adapter):
        for ident, raw, attempts in self.db.execute(
            "SELECT id,body,attempts FROM requests WHERE status='queued' AND due<=?",
            (self.clock(),),
        ).fetchall():
            request = Request.model_validate_json(raw)
            status = "delivered"
            observation = None
            try:
                channel = self.authorize(request)  # revalidate revocation before every retry
                if request.deadline is not None and request.deadline <= self.clock():
                    status = "expired"
                else:
                    operation = request.operation
                    if channel.type == "human" and operation == "request_live_session":
                        try:
                            presence = self.get("presence", channel.channel_id)
                        except PermissionError:
                            presence = {"online": False, "at": 0}
                        if (
                            not presence["online"]
                            or self.clock() - presence["at"] > 60
                            or attempts >= 2
                        ):
                            operation = "send_message"
                            if operation not in channel.capabilities:
                                raise PermissionError("Async fallback is not authorized")
                            with self.db:
                                self.emit(request, "human_unavailable")
                    observation = adapter.send(request, operation)  # adapter must dedupe request_id
            except PermissionError:
                status = "rejected"
            except (OSError, TimeoutError):
                attempts += 1
                if attempts < 3:
                    with self.db:
                        self.db.execute(
                            "UPDATE requests SET attempts=?,due=? WHERE id=?",
                            (attempts, self.clock() + 2**attempts, ident),
                        )
                    continue
                status = "failed"
            with self.db:
                self.db.execute("UPDATE requests SET status=? WHERE id=?", (status, ident))
                self.emit(request, status)
            if status == "delivered" and observation is not None:
                try:
                    if self.artifacts is None:
                        raise ValueError("Artifact store unavailable")
                    data, mime = observation
                    ref, digest, normalized, mime = self.artifacts.put(data, mime)
                    grant = self.get("grant", request.payload["grant_id"])
                    self.observation(ident, grant["session"], ref, digest, normalized)
                    self.put("artifact", digest + ":" + ident, {"request": ident, "mime": mime})
                except (ValueError, PermissionError, OSError):
                    with self.db:
                        self.db.execute("UPDATE requests SET status='failed' WHERE id=?", (ident,))
                        self.emit(request, "failed")

    @synchronized
    def cancel(self, request_id, project):
        row = self.db.execute(
            "SELECT body,status FROM requests WHERE id=?", (request_id,)
        ).fetchone()
        if row is None:
            raise ValueError("Unknown request")
        request = Request.model_validate_json(row[0])
        if request.project_id != project:
            raise PermissionError("Cross-project cancellation")
        if row[1] == "queued":
            with self.db:
                self.db.execute("UPDATE requests SET status='cancelled' WHERE id=?", (request_id,))
                self.emit(request, "cancelled")

    @synchronized
    def observation(self, request_id, session_id, content_ref, digest, data: bytes):
        row = self.db.execute(
            "SELECT body,status FROM requests WHERE id=?", (request_id,)
        ).fetchone()
        if row is None or row[1] != "delivered":
            raise ValueError("Request is not awaiting observation")
        request = Request.model_validate_json(row[0])
        channel = self.authorize(request)
        session = self.session(session_id)
        if session["user"] != channel.owner or session["project"] != request.project_id:
            raise PermissionError("Observation owner mismatch")
        if request.operation not in (
            "request_observation",
            "request_data",
            "send_message",
            "request_live_session",
        ) or not content_ref.startswith("artifact://sha256/"):
            raise ValueError("Immutable observation reference required")
        if (
            len(data) > 5_000_000
            or hashlib.sha256(data).hexdigest() != digest
            or (content_ref != "artifact://sha256/" + digest)
        ):
            raise ValueError("Invalid artifact hash/size")
        with self.db:
            self.emit(request, "response_received", content_ref, digest)
            self.db.execute(
                "UPDATE requests SET status='response_received' WHERE id=?", (request_id,)
            )

    @worker_exclusive
    @synchronized
    def callbacks(self, send):
        for ident, body, attempts in self.db.execute(
            "SELECT id,body,attempts FROM events WHERE sent=0 AND due<=? ORDER BY rowid",
            (self.clock(),),
        ).fetchall():
            timestamp = str(self.clock())
            try:
                send(
                    body.encode(),
                    timestamp,
                    signature(self.transport_key, timestamp, body.encode()),
                )
            except (OSError, TimeoutError):
                with self.db:
                    self.db.execute(
                        "UPDATE events SET attempts=?,due=? WHERE id=?",
                        (attempts + 1, self.clock() + min(300, 2 ** min(attempts + 1, 8)), ident),
                    )
                continue
            with self.db:
                self.db.execute("UPDATE events SET sent=1 WHERE id=?", (ident,))

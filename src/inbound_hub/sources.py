"""Polling adapters; credentials live only in provider instances, never in events."""

from __future__ import annotations

import asyncio
import email
import hashlib
import imaplib
import logging
import re
import time
from datetime import UTC, datetime
from email import policy
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, cast

import httpx

from inbound_hub.events import InboundEvent
from inbound_hub.pipeline import Store


def parse_email(raw: bytes, identity: str, metadata=None):
    msg = email.message_from_bytes(raw, policy=policy.default)
    body = msg.get_body(preferencelist=("plain",))
    attachments = [
        {
            "filename": p.get_filename(),
            "content_type": p.get_content_type(),
            "sha256": hashlib.sha256(cast(bytes, p.get_payload(decode=True) or b"")).hexdigest(),
        }
        for p in msg.iter_attachments()
    ]
    return InboundEvent(
        event_id=hashlib.sha256(identity.encode()).hexdigest(),
        channel="email",
        external_message_id=identity,
        conversation_id=str(msg.get("In-Reply-To") or msg.get("Message-ID") or identity),
        sender=str(msg.get("From", "")),
        subject=str(msg.get("Subject", "")),
        received_at=parsedate_to_datetime(msg["Date"]) if msg.get("Date") else datetime.now(UTC),
        body=body.get_content() if body else "",
        attachments=attachments,
        metadata=metadata or {},
    )


class EmlFolder:
    def __init__(self, folder: Path, metadata=None):
        self.folder, self.metadata = folder.resolve(), metadata or {}

    async def poll(self, checkpoint):
        events = []
        for path in sorted(self.folder.glob("*.eml")):
            if path.is_symlink() or path.stat().st_size > 10_000_000:
                continue
            raw = path.read_bytes()
            events.append(parse_email(raw, hashlib.sha256(raw).hexdigest(), self.metadata))
        return events, checkpoint or ""


class ImapSource:
    def __init__(self, host, user, password, mailbox="INBOX", metadata=None):
        self.host, self.user, self.password, self.mailbox = host, user, password, mailbox
        self.metadata = metadata or {}

    async def poll(self, checkpoint):
        return await asyncio.to_thread(self._poll, checkpoint)

    def _poll(self, checkpoint):
        with imaplib.IMAP4_SSL(self.host, timeout=15) as conn:
            conn.login(self.user, self.password)
            conn.select(self.mailbox, readonly=True)
            validity = conn.response("UIDVALIDITY")[1][0].decode()
            old_validity, _, old_uid = (checkpoint or ":0").partition(":")
            last = int(old_uid) if old_validity == validity else 0
            status, data = conn.uid("search", cast(Any, None), f"UID {last + 1}:*")
            if status != "OK":
                raise OSError("IMAP search failed")
            events = []
            for uid in data[0].split():
                if int(uid) <= last:
                    continue
                size_status, size_rows = conn.uid("fetch", uid, "(RFC822.SIZE)")
                sizes = re.findall(
                    rb"RFC822.SIZE (\d+)", b" ".join(x for x in size_rows if isinstance(x, bytes))
                )
                if size_status != "OK" or len(sizes) != 1 or int(sizes[0]) > 10_000_000:
                    raise ValueError("Email size unavailable or exceeds policy")
                status, rows = conn.uid("fetch", uid, "(BODY.PEEK[])")
                if status != "OK":
                    raise OSError("IMAP fetch failed")
                raw = next(row[1] for row in rows if isinstance(row, tuple))
                if len(raw) > 10_000_000:
                    raise ValueError("Oversized email requires operator handling")
                identity = f"{self.host}/{self.user}/{self.mailbox}/{validity}/{uid.decode()}"
                events.append(parse_email(raw, identity, self.metadata))
                last = max(last, int(uid))
            return events, f"{validity}:{last}"


class SecretLogFilter(logging.Filter):
    def __init__(self, secret):
        super().__init__()
        if not isinstance(secret, str) or not secret.strip():
            raise ValueError("A nonempty secret is required")
        self.secret = secret

    def filter(self, record):
        record.msg = record.getMessage().replace(self.secret, "[REDACTED]")
        record.args = ()
        return True


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str, client=None):
        self.token, self.chat_id = token, chat_id
        logging.getLogger("httpx").addFilter(SecretLogFilter(token))
        self.client = client or httpx.AsyncClient(timeout=10, trust_env=False)

    async def __call__(self, message: str):
        try:
            response = await self.client.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={"chat_id": self.chat_id, "text": message[:4000]},
                follow_redirects=False,
            )
            response.raise_for_status()
            if not response.json().get("ok"):
                raise OSError("Notification rejected")
        except (httpx.HTTPError, ValueError) as exc:
            raise OSError("Notification unavailable") from exc


class AdapterRuntime:
    def __init__(self, store: Store, clock=time.time):
        self.store, self.clock = store, clock
        self.adapters: dict[str, tuple[Any, float]] = {}
        self.status: dict[str, dict[str, Any]] = {}

    def register(self, ident, adapter, interval=30):
        if ident in self.adapters or interval <= 0:
            raise ValueError("Duplicate adapter or invalid interval")
        self.adapters[ident] = (adapter, interval)
        self.status[ident] = {
            "state": "Paused" if self.store.checkpoint("paused:" + ident) == "yes" else "Running",
            "last_check": None,
            "last_success": None,
            "error": None,
            "due": 0.0,
        }

    async def tick(self):
        async def poll(ident, adapter, interval):
            state = self.status[ident]
            if self.store.checkpoint("paused:" + ident) == "yes" or state["due"] > self.clock():
                return
            state["last_check"] = self.clock()
            try:
                events, checkpoint = await asyncio.wait_for(
                    adapter.poll(self.store.checkpoint(ident)), 30
                )
                for event in events:
                    self.store.ingest(event)
                self.store.checkpoint(ident, checkpoint)
                state.update(state="Running", last_success=self.clock(), error=None)
            except Exception as exc:  # noqa: BLE001 - isolate plugins; only exception type is exposed
                # Never persist exception messages containing provider URLs or credentials.
                state.update(state="Error", error=type(exc).__name__)
            state["due"] = self.clock() + interval

        await asyncio.gather(*(poll(i, *spec) for i, spec in self.adapters.items()))

    def pause(self, paused: bool):
        for ident in self.adapters:
            self.store.checkpoint("paused:" + ident, "yes" if paused else "no")
            self.status[ident]["state"] = "Paused" if paused else "Running"


class TelegramSource:
    def __init__(self, token, source_id, allowed_chats, metadata=None, client=None):
        logging.getLogger("httpx").addFilter(SecretLogFilter(token))
        self.token, self.source_id, self.allowed_chats = (
            token,
            source_id,
            set(map(str, allowed_chats)),
        )
        self.metadata = metadata or {}
        self.client = client or httpx.AsyncClient(timeout=15, trust_env=False)

    async def poll(self, checkpoint):
        try:
            response = await self.client.get(
                f"https://api.telegram.org/bot{self.token}/getUpdates",
                params={"offset": int(checkpoint or "0"), "timeout": 0},
                follow_redirects=False,
            )
            response.raise_for_status()
            data = response.json()
            if not data.get("ok"):
                raise OSError("Telegram polling unavailable")
        except (httpx.HTTPError, ValueError) as exc:
            raise OSError("Telegram polling unavailable") from exc
        events, offset = [], int(checkpoint or "0")
        for update in data["result"]:
            offset = max(offset, update["update_id"] + 1)
            msg = update.get("message", {})
            chat = str(msg.get("chat", {}).get("id", ""))
            if chat not in self.allowed_chats or not msg.get("text"):
                continue
            identity = f"{self.source_id}:{chat}:{msg['message_id']}"
            events.append(
                InboundEvent(
                    event_id=hashlib.sha256(identity.encode()).hexdigest(),
                    channel="telegram",
                    external_message_id=identity,
                    conversation_id=chat,
                    sender=str(msg.get("from", {}).get("id", "")),
                    body=msg["text"],
                    received_at=datetime.fromtimestamp(msg["date"], UTC),
                    metadata=self.metadata,
                )
            )
        return events, str(offset)


class FolderSource:
    """Text/JSON observations only; documents/binaries remain attachment workflows."""

    def __init__(self, folder: Path, metadata=None):
        self.folder, self.metadata = folder.resolve(), metadata or {}

    async def poll(self, checkpoint):
        events = []
        for path in sorted(self.folder.iterdir()):
            if path.suffix not in (".txt", ".json") or path.is_symlink() or not path.is_file():
                continue
            if path.stat().st_size > 1_000_000:
                raise ValueError("Folder item exceeds size limit")
            raw = path.read_bytes()
            body = raw.decode("utf-8")
            identity = hashlib.sha256(str(path).encode() + b"\0" + raw).hexdigest()
            events.append(
                InboundEvent(
                    event_id=identity,
                    channel="folder",
                    external_message_id=identity,
                    received_at=datetime.fromtimestamp(path.stat().st_mtime, UTC),
                    subject=path.name,
                    body=body,
                    metadata=self.metadata,
                )
            )
        return events, checkpoint or ""

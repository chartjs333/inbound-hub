"""Public-key verification and immutable, validated observation artifacts."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
import wave
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from PIL import Image


class TrustStore:
    """Operator-pinned Ed25519 public keys, separated by purpose; supports rotation/revocation."""

    def __init__(self, keys: dict[str, dict[str, bytes]]):
        self.keys = keys

    def verify(self, purpose: str, message: bytes, signature: str):
        try:
            key_id, encoded = signature.split(".", 1)
            key = self.keys[purpose][key_id]
            Ed25519PublicKey.from_public_bytes(key).verify(
                base64.b64decode(encoded, validate=True), purpose.encode() + b"\0" + message
            )
        except (KeyError, ValueError, InvalidSignature) as exc:
            raise PermissionError("Untrusted or revoked signature") from exc


class ArtifactStore:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)

    def put(self, data: bytes, mime: str):
        try:
            return self._put(data, mime)
        except (wave.Error, EOFError, OSError, Image.DecompressionBombError) as exc:
            raise ValueError("Invalid observation media") from exc

    def _put(self, data: bytes, mime: str):
        if not data or len(data) > 5_000_000:
            raise ValueError("Empty or oversized observation")
        if mime in ("image/png", "image/jpeg"):
            with Image.open(io.BytesIO(data)) as image:
                if image.width * image.height > 16_000_000:
                    raise ValueError("Image dimensions exceed limit")
                image.load()
                output = io.BytesIO()
                image.convert("RGB").save(output, format="PNG")
                data, mime = output.getvalue(), "image/png"
        elif mime == "audio/wav":
            with wave.open(io.BytesIO(data)) as audio:
                if (
                    audio.getnchannels() not in (1, 2)
                    or audio.getsampwidth() != 2
                    or (
                        audio.getframerate() not in (16000, 44100, 48000)
                        or audio.getnframes() / audio.getframerate() > 60
                    )
                ):
                    raise ValueError("Unsupported audio format or duration")
                if len(audio.readframes(audio.getnframes())) != (
                    audio.getnframes() * audio.getnchannels() * audio.getsampwidth()
                ):
                    raise ValueError("Truncated audio")
        elif mime == "application/json":
            parsed = json.loads(data)
            data = json.dumps(parsed, allow_nan=False, sort_keys=True).encode()
        elif mime == "text/plain":
            data.decode("utf-8")
        else:
            raise ValueError("Unsupported observation media type")
        if len(data) > 5_000_000:
            raise ValueError("Decoded artifact exceeds limit")
        digest = hashlib.sha256(data).hexdigest()
        path = self.root / digest
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError("Artifact integrity failure")
        else:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        return "artifact://sha256/" + digest, digest, data, mime

    def read(self, digest: str):
        if not re.fullmatch("[a-f0-9]{64}", digest):
            raise ValueError("Invalid artifact digest")
        path = self.root / digest
        if path.is_symlink():
            raise ValueError("Invalid artifact path")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("Artifact integrity failure")
        return data

"""Service factory. Starts only with configured public-key trust and live authorization."""

import asyncio
import base64
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn

from .adapters import ChannelRouter, MobileInboxAdapter, ReadOnlyHttpAdapter
from .api import create_app
from .gateway import Gateway
from .introspection import ActiveAssignmentClient
from .models import Channel, Plugin
from .security import ArtifactStore, TrustStore
from .transport import CallbackClient


def main():
    os.umask(0o077)
    config = json.loads(Path(os.environ["BRIDGE_CONFIG"]).read_text())
    keys = {
        purpose: {ident: base64.b64decode(value, validate=True) for ident, value in items.items()}
        for purpose, items in config["public_keys"].items()
    }
    introspection = ActiveAssignmentClient(
        config["assignment_endpoint"], os.environ["BRIDGE_ASSIGNMENT_TOKEN"]
    )
    gateway = Gateway(
        config["database"],
        base64.b64decode(os.environ["BRIDGE_TRANSPORT_KEY"], validate=True),
        os.urandom(32),
        os.urandom(32),
        introspection,
        trust=TrustStore(keys),
    )
    artifacts = ArtifactStore(Path(config["artifacts"]))
    gateway.artifacts = artifacts
    adapters: dict[str, Any] = {}
    for item in config["channels"]:
        channel = Channel(**item)
        gateway.register_channel(channel)
        if channel.type == "human":
            adapters[channel.channel_id] = MobileInboxAdapter()
    for item in config.get("read_only_endpoints", []):
        token = os.environ[item["token_env"]] if item.get("token_env") else None
        adapters[item["channel_id"]] = ReadOnlyHttpAdapter(item["endpoint"], token)
    for item in config.get("plugins", []):
        gateway.register_plugin(Plugin(**item["manifest"]), item["signature"])
    for item in config.get("checkpoints", []):
        gateway.register_checkpoint(**item)
    callback = CallbackClient(config["callback_endpoint"])
    router = ChannelRouter(adapters)
    app = create_app(
        gateway, artifacts=artifacts, idp_url=config["identity_provider"], origin=config["origin"]
    )
    stop = asyncio.Event()
    health = {"worker": "starting"}

    async def worker():
        while not stop.is_set():
            try:
                await asyncio.to_thread(gateway.dispatch, router)
                await asyncio.to_thread(gateway.callbacks, callback)
                health["worker"] = "running"
            except (OSError, ValueError):
                health["worker"] = "error"
            try:
                await asyncio.wait_for(stop.wait(), 1)
            except TimeoutError:
                pass

    @asynccontextmanager
    async def lifespan(app):
        task = asyncio.create_task(worker())
        try:
            yield
        finally:
            stop.set()
            await task
            callback.close()
            introspection.client.close()
            gateway.close()

    app.router.lifespan_context = lifespan

    @app.get("/health")
    def status():
        return health

    uvicorn.run(app, host="127.0.0.1", port=config.get("port", 8081))


if __name__ == "__main__":
    main()

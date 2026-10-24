"""Configured service launcher; credentials are environment references, never config values."""

import json
import os
from pathlib import Path
from typing import Any

import uvicorn

from inbound_hub.coordinator import Coordinator
from inbound_hub.domains.musician import MusicianBookingPlugin, Profiles
from inbound_hub.domains.registry import DomainPluginRegistration, DomainPluginRegistry
from inbound_hub.integrations.nginx_qa import NginxQaClient, NginxQaProposalTarget
from inbound_hub.pipeline import Pipeline, ProjectBinding, Store
from inbound_hub.service import create_service
from inbound_hub.sources import (
    AdapterRuntime,
    EmlFolder,
    FolderSource,
    ImapSource,
    TelegramNotifier,
    TelegramSource,
)


def configured_app(restart_request=None):
    os.umask(0o077)
    config = json.loads(Path(os.environ["HUB_CONFIG"]).read_text())
    producer = os.environ["HUB_PRODUCER_TOKEN"]
    control = os.environ["HUB_CONTROL_TOKEN"]
    mail_password = os.environ.get("HUB_IMAP_PASSWORD", "")
    telegram = os.environ.get("HUB_TELEGRAM_TOKEN", "")
    store = Store(
        config["database"], tuple(filter(None, (producer, control, mail_password, telegram)))
    )
    plugin = MusicianBookingPlugin(
        Profiles(Path(config["profiles_repository"]), config["profiles_ref"]),
        config.get("artist_mappings", {}),
    )
    registry = DomainPluginRegistry()
    registry.register(DomainPluginRegistration(plugin.metadata, plugin))
    target = NginxQaClient(
        NginxQaProposalTarget(config["nginx_url"], config["project_id"]), producer
    )
    notifier = TelegramNotifier(telegram, config["telegram_chat_id"]) if telegram else None
    pipeline = Pipeline(
        store,
        Coordinator(registry),
        ProjectBinding("musician-booking", config["candidate"], config.get("role_bindings", {})),
        target,
        notifier,
    )
    runtime = AdapterRuntime(store)
    adapter: Any
    for source in config["sources"]:
        if source["type"] == "eml-folder":
            adapter = EmlFolder(Path(source["folder"]), source.get("metadata"))
        elif source["type"] == "folder":
            adapter = FolderSource(Path(source["folder"]), source.get("metadata"))
        elif source["type"] == "imap":
            adapter = ImapSource(
                source["host"],
                source["user"],
                mail_password,
                source.get("mailbox", "INBOX"),
                source.get("metadata"),
            )
        elif source["type"] == "telegram":
            adapter = TelegramSource(
                telegram, source["id"], source["allowed_chats"], source.get("metadata")
            )
        else:
            raise ValueError("Unsupported source type")
        runtime.register(source["id"], adapter, source.get("interval", 30))
    return create_service(pipeline, runtime, control, restart_request), config.get("port", 8080)


def main():
    app, port = configured_app()
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()

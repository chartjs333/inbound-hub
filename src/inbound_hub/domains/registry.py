from __future__ import annotations

from dataclasses import dataclass, field

from inbound_hub.domains.contracts import DomainPlugin, DomainPluginMetadata


@dataclass
class DomainPluginRegistration:
    metadata: DomainPluginMetadata
    plugin: DomainPlugin


@dataclass
class DomainPluginRegistry:
    _items: dict[str, DomainPluginRegistration] = field(default_factory=dict)

    def register(self, registration: DomainPluginRegistration) -> None:
        plugin_id = registration.metadata.plugin_id
        if plugin_id in self._items:
            raise ValueError(f"domain plugin already registered: {plugin_id}")
        self._items[plugin_id] = registration

    def get(self, plugin_id: str) -> DomainPluginRegistration:
        return self._items[plugin_id]

    def list(self) -> list[DomainPluginRegistration]:
        return list(self._items.values())

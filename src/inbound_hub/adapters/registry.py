from __future__ import annotations

from dataclasses import dataclass, field

from inbound_hub.adapters.contracts import AdapterFactory, AdapterMetadata


@dataclass
class AdapterRegistration:
    metadata: AdapterMetadata
    factory: AdapterFactory


@dataclass
class AdapterRegistry:
    _items: dict[str, AdapterRegistration] = field(default_factory=dict)

    def register(self, registration: AdapterRegistration) -> None:
        adapter_id = registration.metadata.adapter_id
        if adapter_id in self._items:
            raise ValueError(f"adapter already registered: {adapter_id}")
        self._items[adapter_id] = registration

    def get(self, adapter_id: str) -> AdapterRegistration:
        return self._items[adapter_id]

    def list(self) -> list[AdapterRegistration]:
        return list(self._items.values())

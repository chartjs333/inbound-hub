"""Source-neutral coordinator using the existing domain plugin SDK."""

from typing import Any

from inbound_hub.domains.registry import DomainPluginRegistry
from inbound_hub.events import InboundEvent


class Coordinator:
    def __init__(self, registry: DomainPluginRegistry):
        self.registry = registry

    async def handle(self, event: InboundEvent, plugin_id: str):
        plugin = self.registry.get(plugin_id).plugin
        context: dict[str, Any] = {}
        extraction = await plugin.extract(event, context)
        classification = await plugin.classify(extraction, context)
        escalation = await plugin.escalate(extraction, classification, context)
        proposal = (
            None
            if escalation.required
            else await plugin.propose(extraction, classification, context)
        )
        return {"context": extraction.data, "proposal": proposal, "escalation": escalation}

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
        extracted_route = extraction.data.get("route")
        if not isinstance(extracted_route, str):
            extracted_route = "clarification_required"
        route = {"pending_proposal": "new_sprint", "correspondence": "correspondence_only"}.get(
            extracted_route, extracted_route
        )
        update_intent = None
        # Only operator-bound source metadata identifies an existing sprint; message text cannot.
        if proposal and event.metadata.get("sprint_id"):
            route = "sprint_update"
            update_intent = {
                "sprint_id": event.metadata["sprint_id"],
                "status": "requires_review",
                "context": extraction.data,
            }
            proposal = None
        return {
            "context": extraction.data,
            "proposal": proposal,
            "escalation": escalation,
            "route": route,
            "update_intent": update_intent,
        }

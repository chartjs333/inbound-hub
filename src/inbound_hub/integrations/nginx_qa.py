"""nginx-qa integration boundary.

The concrete API contract will be aligned with the nginx-qa inbound-integration sprint.
Inbound Hub must not reach into nginx-qa runtime files directly.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NginxQaProposalTarget:
    base_url: str
    project_id: str

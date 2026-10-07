# nginx-qa Integration Contract — Consumer Side

Inbound Hub treats nginx-qa as an external service.

Expected capabilities from nginx-qa:
- idempotent create-pending-proposal API;
- read proposal/status;
- existing Pending Sprints UI;
- Preview / Reject / Play activation boundary;
- managed start-from-git bridge where proposal points to Git manifest;
- stable error codes and correlation IDs.

Inbound Hub must submit only source-neutral proposal metadata. Source credentials must never cross this boundary.

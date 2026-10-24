# Branch dependency audit and implementation roadmap

Snapshot: 2026-10-24. Repository: chartjs333/inbound-hub. No existing PRs at audit.

| Branch | Head | Relationship |
|---|---|---|
| main | ff1e5a34324c7a6662c8009d1ed1b8416468feef | Common ancestor of both requested branches |
| codex/musician-booking-adapter-v1 | 84477f2c0e4580f48a5fa8c66e1e78a5f200dad2 | 23 commits beyond common ancestor; Python scaffold + booking specifications |
| spec/agent-channel-bridge-v1 | bc03e7ca6de7255c6011bc47bb57d699d4dc60ae | 9 commits beyond common ancestor; three specification files only |
| codex/inbound-hub-bootstrap | dd8ef776b6ec38112b2b6e1d815e0d2f255084d1 | Diverges from musician branch at 462d79ffce6f9e92aa19404679328b5accf1d885; 12 bootstrap-only / 10 musician-only commits |

Both requested branches share identical README and .gitignore; feature files do not overlap.
Bootstrap contains existing DomainPlugin contracts/registry that must be reused, not redesigned.
The musician working branch carries the original four SDK changes (a3549ae, 7525642,
a91d31c, f376a21) with original commit provenance credited in the implementation commit. Other bootstrap functionality is not copied.
When bootstrap is integrated later, retain these same SDK files, not a second registry.

## Order and ownership

1. Complete booking models, conservative extraction, deterministic artist selection,
   committed profile provenance and pending proposal generation. Implemented in
   `work/musician-booking-completion`, based on and targeting `codex/musician-booking-adapter-v1`.
2. Implement isolated bridge lifecycle, registry, authenticated transport, authorization,
   sessions, read-only simulation and evidence. Implemented in `work/channel-bridge-completion`,
   based on and targeting `spec/agent-channel-bridge-v1`.
3. Run checks separately and together. Bridge lives in its own `channel_bridge/` distribution
   and imports no inbound/domain code. There is no dependency between the two implementation PRs.
4. Review protocol with nginx-qa owner and qualify real integrations/hardware: external follow-up,
   not claimed complete by simulation. Do not merge or deploy automatically.

## Musician scope and limitations

Implemented: typed context/taxonomy, canonical JSON, all domain fields, missing-value semantics,
conservative keyword classifier, labelled extraction plus unambiguous ISO date/currency extraction,
explicit/mapped artist resolution, ambiguity rejection, committed shared/artist profile loader,
artist constraints, six specialist proposal roles, SDK/coordinator handoff and source parity tests.

The resolver never selects an artist from message inference. Exact display-name matches are suggestions only; unsupported/ambiguous free text requires operator
clarification. Dates like “next Friday”, inferred venue names, inferred currency and price ranges
are intentionally not guessed. Real artist profiles and mappings must be supplied by the operator;
tests create two synthetic, committed artist repositories. No credentials or personal profiles ship.

The coordinator is a library integration point: construct Profiles(repo, ref), MusicianBookingPlugin,
DomainPluginRegistration and Coordinator, then await handle(event, 'musician-booking').
The existing health API is retained. No external send, sprint activation or nginx-qa submission occurs.
Production ingestion wiring, nginx-qa contract qualification and human domain review remain external.

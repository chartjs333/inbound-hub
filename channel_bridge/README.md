# Agent Channel Bridge v1 — simulation implementation

This independently packaged subsystem implements the inbound-hub side of
`../specs/001-agent-channel-bridge/`. It does not import the musician plugin, copy
InboundEvent or alter proposal/Play/Start behavior.

## Run checks

From `channel_bridge/`, install `python -m pip install -e '.[dev]'`, then run:

```
python -m pytest -q
python -m ruff check --config pyproject.toml src tests
python -m mypy --ignore-missing-imports --check-untyped-defs src
python -m build --no-isolation
```

Use `Gateway(path, transport_key, identity_key, plugin_key, active_assignment)`.
Keys must be independently supplied from an operator secret store (32+ bytes); none
are stored in SQLite. Registry, presence, grants, session and challenge methods are
trusted application methods, NOT unauthenticated public admin endpoints.
`create_app(gateway)` exposes only signed `/v1/channel-requests` intake.
An operator-controlled single dispatcher calls `dispatch(adapter)` and
`callbacks(CallbackClient(configured_https_endpoint))` periodically.
TLS termination, secret storage/rotation, worker scheduling and authenticated user
UI integration are deployment responsibilities, not enabled by this package.

## Implemented / simulated

- Strict versioned request/event models; channel capabilities and project/agent scope.
- Signed intake and callback delivery; timestamp checks, immutable request identity,
  durable SQLite request/event outboxes, retry backoff and callback event IDs.
- Active-assignment validation is an injected trusted policy checked at intake and dispatch.
- Owner-controlled human presence; stale/unknown presence is Offline; no Offline calls;
  two failed live-session attempts fall back to asynchronous delivery.
- Trusted QR lookup and signed approved plugin manifests, compatibility/minimum version,
  consented activation distinct from permission to execute. Android/iOS install sources
  are restricted to platform stores; server modules are built-ins. No executable QR data.
- Human/agent entitlement intersection, device/action/session-scoped grants, expiry,
  revocation, assurance and action-bound step-up, challenge attempt limit/replay rejection.
- Single-tap cryptographic identity-provider assertion simulation; static card UID/PIN rejected.
  Session idle/absolute expiry, logout/admin/lost-card revoke via `revoke`, and workstation
  user switch. No continuous card presence is required.
- Read-only device/human/service adapter simulation, artifact digest/size checking,
  correlated response events with project/sprint/assignment/agent, experiment/checkpoint,
  sample, instrument and operator lineage. Content remains untrusted inert data.
- HTTP intake and HTTPS callback integration tested in memory. Request and callback retries
  require idempotent remote adapters/inboxes; this is at-least-once delivery, not exactly-once.

## Remaining qualification and limitations

This is a reviewable simulator MVP, not production activation. The nginx-qa wire contract
has NOT been frozen with that repository's owner or tested against a disposable real sprint.
Timestamps currently use UTC Unix seconds and HMAC SHA-256 over `timestamp + '.' + body`;
both repositories must explicitly agree before integration. Callback receivers must dedupe
by event_id and tolerate reordered accepted/delivered events during outages.

There is no native Android/iOS application, store package installation, live call provider,
camera capture, real microscope or card-reader driver in this PR. Simulator fixtures exercise
the server flow; real-device qualification must verify signed platform packaging, consent UI,
IdP smart-card challenge binding, trusted workstation identity, physical disconnect behavior,
media MIME/codec scanning and platform secure storage. Artifact content is verified but is not
uploaded to an external immutable store by this package. Provision and validate that store
before supplying real artifact references. Sensitive content must not enter audit logs.

Only one dispatcher may own a database; multi-worker leasing, distributed rate
limiting, key rotation and production-grade audit/export/retention still need hardening.
Cryptographic IdP/plugin signature trust is simulated with distinct HMAC trust keys, not a
hardware attestation or public-key plugin signing infrastructure. No physical control exists.

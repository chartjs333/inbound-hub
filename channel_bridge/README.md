# Inbound Agent Channel Bridge — Draft, not production-ready

Independent package, based on `spec/agent-channel-bridge-v1`. It does not copy or import the
Inbound Hub coordinator, and never calls Play/Start. Production readiness is blocked as listed below.

## Implemented

- Strict v1 request/event schemas, bounded signed intake, project/agent/action authorization.
- SQLite request/event outboxes, deduplication, retry/backoff, deadline/cancel, correlated results.
  File locking serializes competing delivery workers; adapters/receivers must dedupe remote effects.
- Owner-controlled Online/Offline with TTL, async fallback without capability bypass.
- QR discovery of registered checkpoints; signed plugin approval, device compatibility and explicit
  activation consent. Grants bind session/agent/device/plugin version+hash/action and assurance.
- Ed25519 purpose-separated identity/plugin verification, key rotation by pinned trust registry,
  proof replay/attempt/rate limits, step-up, session expiry, revoke and workstation user switch.
  Removing a trust key invalidates affected sessions/plugins on subsequent checks. PIN fields rejected.
- Mobile responsive web UI at `/mobile`: IdP popup login, session/logout, channels and presence,
  QR scanner with manual fallback, approved store links, activation, action-bound step-up/grants,
  request inbox, text/file responses, camera photo capture and bounded WAV voice recording.
  Credentials remain in secure HttpOnly SameSite cookies; CSRF+Origin+CSP enforced. No offline auth cache.
- Immutable SHA-256 artifact storage; bounded text/JSON/PNG/JPEG/WAV validation, image metadata stripping,
  per-request owner/project access, instrument/operator/sample/experiment lineage. SVG/HTML rejected.
- Production mobile inbox and configured read-only HTTPS data adapters; no physical actuation.
  Live calls without a configured provider fail and follow the bounded async fallback path.
- Live assignment introspection client is fail-closed on missing/invalid/downstream responses.
  HTTPS callback client never derives destinations from source payloads.

## Entry point and trust contract

Install `python -m pip install -e '.[dev]'`; run `python -m agent_channel_bridge` only when explicitly
starting the configured service. Nothing is deployed by installation/tests.
`BRIDGE_CONFIG` references protected JSON: database, artifacts, public_keys (identity/plugin maps of
key ID to base64 Ed25519 public key), identity_provider, origin, assignment_endpoint, callback_endpoint,
channels, signed plugins, checkpoints, optional read_only_endpoints and port.
Secrets: `BRIDGE_TRANSPORT_KEY` (base64, 32+ bytes), `BRIDGE_ASSIGNMENT_TOKEN`, and optional adapter token
environment references. No signing private keys are stored in the Hub. Launcher applies umask 077.
Origin/IdP/device/callback endpoints require HTTPS; uvicorn listens only on loopback behind an
operator-configured TLS proxy. Trusted registry administration is not exposed as a public HTTP API.

The trusted IdP receives challenge+binding via the configured popup URL and returns
`{proof, signature}` with `postMessage` to the exact Hub origin. Signature format is
`key_id.base64(Ed25519.sign(b'identity\0' + canonical(proof)))`, where `canonical` is the exported
sorted-key JSON helper and `\0` denotes one NUL byte. Proof binds user/project/workstation/action,
device/plugin/session/nonce/expiry and cryptographically verified method/assurance. No static UID/PIN
counts as proof. The IdP must authenticate the user and trusted workstation before signing.
Plugin signatures use purpose `plugin` + NUL + `plugin_message(manifest)`; this helper sorts set fields.

Assignment introspection POSTs project_id/sprint_id/assignment_id/agent_id using a scoped Bearer token.
Only an exact matching response with `active: true` authorizes work. This is a proposed bridge
integration contract, NOT an endpoint known to exist in nginx-qa. No permissive fallback exists.
Callbacks use X-Timestamp and X-Signature HMAC SHA-256 over timestamp + '.' + exact bytes.
Persisted callbacks must be deduped by event_id and may arrive out of order after network failures.

## Verification

```
python -m pytest -q
python -m ruff check --config pyproject.toml src tests
python -m mypy --ignore-missing-imports --check-untyped-defs src
python -m build --no-isolation
python -m bandit -r src
python -m pip_audit --disable-pip --no-deps -r requirements-runtime.lock
```

Browser tests additionally need Playwright and `HUB_TEST_CHROMIUM`. `python scripts/verify_release.py`
fails if the browser prerequisite is absent. Default pytest skips the browser test; that is NOT
production qualification. See VALIDATION.md for the separately attempted browser failure.

## Exact open requirements / blockers

- nginx-qa main `627b478e29f5f7254d279363790f46e92c114d8d` has pending proposal APIs but no implemented
  agent-channel callback/introspection counterpart. Its bridge branch contains specs only. Real
  active-sprint E2E is blocked without a counterpart; nginx-qa was not modified.
- No trusted production IdP endpoint/key, device endpoints, callback endpoint or deployment credentials
  supplied. Test keys and simulators are fixtures only. Do not substitute them in production.
- Chromium E2E failed to launch in this execution environment (SIGTRAP/exit 133); browser UI acceptance
  is not complete. JS syntax and server functional/security tests pass; these are not a visual/UI pass.
- Native mobile store package signing/delivery and installed-module attestation are not implemented.
  Web UI supports the permitted web workflow, discovery and consent; it cannot attest native installation.
- Real telephony/WebRTC provider, smart-card reader/IdP, camera/microphone platform and physical
  microscope qualification remain external. Hardware simulations do not establish hardware readiness.
- Full production distributed authorization/state replication, operational audit export/retention,
  backup/restore drills, load/soak tests and independent penetration review remain outstanding.
  The provided launcher uses one application process with bounded polling and serialized delivery.

Required hardware/platform tests: genuine card challenge + lost-card revoke + workstation switch;
Android/iOS consent and capture lifecycle; camera privacy/EXIF removal; microphone duration/format;
QR spoofing/physical label swap; approved plugin/device identity; microscope read calibration and
instrument disconnect/reconnect; Offline no-call with real provider. No instrument actuation allowed.

Both PRs remain Draft; no merge or deployment. Passing unit/security scans is necessary but insufficient
for declaring the project production-ready.

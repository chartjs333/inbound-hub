# Implementation status, 2026-10-24

Source/base/target: `spec/agent-channel-bridge-v1` at bc03e7ca6de7255c6011bc47bb57d699d4dc60ae.
Working branch: `work/channel-bridge-completion`. No merge or deployment.

The musician branch (84477f2) and this branch share ff1e5a3, which is also main.
They have 23 and 9 exclusive commits respectively and no feature-file overlap.
Musician uses the existing bootstrap DomainPlugin SDK; bridge is a separate distribution
under `channel_bridge/`, with no copied inbound models or coordinator. Neither implementation
PR depends on the other. Review musician first, then bridge; integrate only by explicit review.

## Current requirements and evidence

| Original task | Implemented / remaining qualification |
|---|---|
| Survey inbound boundary | Complete: isolated distribution; no duplicated domain SDK |
| Freeze wire schemas with nginx-qa | Typed schemas and fail-closed live introspection client; server counterpart absent, cross-repo contract acceptance blocked |
| Registry, intake, durable dispatch | SQLite outboxes, concurrent dedupe, worker file locks, retry/cancel/deadlines; local persistence/backup-restore tests pass |
| Mobile presence, messaging | Responsive web UI, authenticated HTTP API, presence/inbox/text/camera/WAV/file; browser acceptance blocked by Chromium launch failure; real calling provider absent |
| QR, observations, artifact refs | Registered discovery, immutable digest storage, media validation/normalization, scoped download and lineage; real device validation pending |
| Read-only devices | Configured HTTPS GET adapter plus microscope simulator, correlated observation; physical calibration/driver acceptance pending |
| Authenticated callbacks/retries | Configured HTTPS transport with signatures and retry; actual nginx-qa active-agent callback receiver absent |
| Existing inbound regression | Independently tested packages; real nginx-qa pending-proposal integration in PR #1, not evidence for bridge counterpart |
| HUB-10 signed plugin discovery | Ed25519 purpose-separated pinned trust, deterministic manifest signature, key revocation; production signed catalog pending |
| HUB-11 installation/activation | Store links, compatibility, explicit consent and version/hash binding; native package delivery/installed-module attestation not implemented |
| HUB-12 capability broker | Session/user/agent/device/plugin/action grants, assurance/freshness/expiry/revoke; async fallback rechecks scope |
| HUB-13 negative security cases | Forged signature/QR, replay, cross-project, stale/revoked grants/keys, CSRF/Origin, upload bounds, PIN rejection and concurrent intake tested; independent penetration review pending |
| HUB-14 microscope end-to-end | Simulator and read-only HTTP observation tested; physical instrument and active nginx-qa flow unqualified |
| HUB-15 smart-card login | Signed external IdP proof and popup contract; real card reader/IdP integration unavailable |
| HUB-16 session assurance | HttpOnly secure cookies, CSRF, rate limits, step-up, idle/absolute expiry, logout/revoke/user switch; real IdP/platform acceptance pending |

## Mandatory gates

43 server/unit/functional/security tests pass; one browser test is skipped in the default suite.
The explicitly enabled Chromium run failed before page launch (SIGTRAP/exit 133), so the browser gate
is **not passed**. Ruff, mypy, wheel/sdist build, Bandit and runtime dependency audit pass.
Pillow was upgraded to 13.0.0 after the audit found advisories in 12.3.0; re-audit reports none.
No independent penetration assessment, production load/soak test or operational disaster recovery
drill has been completed. No production endpoint, signing key or physical device was substituted
with a fixture and represented as qualified.

See [README](../../channel_bridge/README.md) for configuration, trust contract and the exact
hardware/platform acceptance list, and [VALIDATION](../../channel_bridge/VALIDATION.md) for commands
and actual outputs. Source task checkboxes remain unchanged because local tests cannot complete
native/platform or cross-repository acceptance. **Not production-ready; PR remains Draft.**

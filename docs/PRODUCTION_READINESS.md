# Production readiness — NOT READY

Snapshot: 2026-10-24. PR remains Draft. No merge, deployment, source-branch update or
nginx-qa repository change is authorized/performed. This supersedes the initial MVP status.

## Implemented requirements and evidence

| Requirement | Implementation and qualification |
|---|---|
| HUB-002 normalized events, dedupe, persistence | SQLite WAL event store, source identity conflict rejection, credential-key/value rejection, restart test |
| HUB-003 Email ingestion | TLS IMAP UIDVALIDITY/UID checkpoints, read-only polling and size gate; fake IMAP tests and real email parsing |
| HUB-004 adapter lifecycle | Independent async polling with timeout, Running/Paused/Error, checkpoints, persisted pause; one source failure does not stop others |
| HUB-005 coordinator | Domain SDK handoff, correspondence/clarification recording; no autonomous replies. Existing-sprint metadata produces review-only update intents; domain handlers remain pluggable |
| HUB-006 proposal synthesis | Stable project/source idempotency, lineage, configured legacy/managed candidate; six booking roles with operator-supplied identities, fields/constraints/profile commit |
| HUB-007 nginx-qa client | Real pending-sprints v1 create/status API, Bearer auth, correlation, duplicate create, classified retry/backoff; no activation method |
| HUB-008 notifications | Durable notification queue; Telegram failures isolated; provider token redacted from HTTP logs; status messages contain no raw source content |
| HUB-009 service | Background pipeline, authenticated local control/status, graceful shutdown, environment-only credentials, service entry point and lifecycle tests |
| HUB-010 tray | Independent optional pystray shell: status, open API UI, pause/resume, restart service, exit; mock service tests. Optional SCM host and explicit service restart callback implemented; real Windows acceptance remains pending |
| HUB-011 integration | Real unchanged nginx-qa ASGI code: synthetic Email → booking → six actors → pending proposal → dedupe → not_started status; invalid token rejected |
| MUSIC-001–008 | Typed context, intent rules, conservative fields, committed profiles, artist binding, specialist proposals, coordinator plugin, source parity and synthetic multi-artist tests |

## Exact nginx-qa boundary tested

Read-only checkout of `chartjs333/nginx-qa` main at
`627b478e29f5f7254d279363790f46e92c114d8d`.
Actual server application and schema/auth/persistence code were imported unchanged. Its data paths
were redirected to test temporary directories. The real remote/staging server was not contacted.
Tests call only POST `/api/v1/projects/{project_id}/pending-sprints` and GET
`/api/v1/projects/{project_id}/pending-sprints/{pending_id}/status`. Play/Start is never invoked.
nginx-qa git status remained clean after tests. Producer registry uses real filesystem permission checks.

## Running without deployment

Install the package with `python -m pip install -e '.[dev]'`; optional Windows tray is `.[tray]`.
The version snapshot for runtime dependencies is `requirements-runtime.lock`; the lock has versions,
not wheel hashes. `python -m inbound_hub` starts a loopback-only service when explicitly run.
Set `HUB_CONFIG` to operator configuration, plus `HUB_PRODUCER_TOKEN` and `HUB_CONTROL_TOKEN`.
IMAP/Telegram use `HUB_IMAP_PASSWORD` and `HUB_TELEGRAM_TOKEN`; never put these values in JSON/Git.
Config fields: database, profiles_repository, profiles_ref, artist_mappings, nginx_url, project_id,
candidate, optional role_bindings, sources, optional telegram_chat_id and port.
Sources: `imap` (host/user/mailbox), `eml-folder` (folder), `folder` (UTF-8 text/JSON) and `telegram` (allowed_chats).
The production launcher uses umask 077. Protect existing state/config with equivalent Windows ACLs.
Tray exiting does not stop the service. The optional `inbound-hub-windows` entry point hosts the service under SCM and supports explicit restart requests. Without a configured service manager, restart returns 503. No service installation was executed.

## Open requirements / release blockers

1. Channel Bridge counterpart in nginx-qa is absent: its `spec/agent-channel-bridge-v1` branch adds
   only three spec documents to main. Pending-proposal integration passing does NOT establish
   active-agent callback/introspection support. Do not invent or enable those routes.
2. Staging URL, scoped producer credentials, real operator profiles/mappings and signed manifests
   are not available; live deployment/operational acceptance has not been performed.
3. Windows SCM host and tray entry points are implemented but has only mock lifecycle tests on Linux.
   Native Windows installation, SCM recovery, ACL and interactive tray acceptance remain mandatory.
   General non-booking domains require their own plugins; Folder ingestion supports text/JSON/EML,
   not arbitrary binary document interpretation.
4. Booking text extraction remains conservative rules/explicit labels, with unambiguous ISO dates
   and amounts; no broad natural-language accuracy qualification or human domain sign-off.
5. Mobile browser E2E is not passed (see Bridge report). Safari/Android device acceptance, trusted
   IdP and hardware tests are outstanding.
6. Independent security review, load/soak tests, backup/restore and disaster recovery drills,
   retention policy and production TLS/secret rotation/monitoring acceptance remain outstanding.

Run `python scripts/verify_release.py` for local automated checks; no external checkout is required.
The previous in-process nginx-qa test has been replaced by consumer HTTP contract tests.
Historical server-code results above are not current live interoperability evidence.
Passing this script alone does not satisfy the external/manual checks above. Production-ready must
not be claimed until every required check has evidence. See `VALIDATION.md`, `SECURITY_SCAN.json`
and `DEPENDENCY_AUDIT.json` for actual results, not inferred readiness.

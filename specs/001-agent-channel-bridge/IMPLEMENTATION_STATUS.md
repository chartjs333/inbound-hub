# Implementation status, 2026-10-24

Source/base/target: `spec/agent-channel-bridge-v1` at bc03e7ca6de7255c6011bc47bb57d699d4dc60ae.
Working branch: `work/channel-bridge-completion`. No merge or deployment.

The musician branch (84477f2) and this branch share ff1e5a3, which is also main.
They have 23 and 9 exclusive commits respectively and no feature-file overlap.
Musician uses the existing bootstrap DomainPlugin SDK; bridge is a separate distribution
under `channel_bridge/`, with no copied inbound models or coordinator. Neither implementation
PR depends on the other. Review musician first, then bridge; integrate only by explicit review.

| Original task | Status / evidence |
|---|---|
| Survey inbound boundary | Complete: branch has specs only; isolation preserves existing path |
| Freeze wire schemas with nginx-qa | Draft Pydantic schemas implemented; cross-repo agreement remains pending |
| Registry, intake, durable dispatch | Implemented and simulator-tested |
| Mobile presence, messaging | Server flow + simulator implemented; native UI/provider not implemented |
| QR, observations, artifact refs | Implemented with checksum/size validation; external artifact storage/media scanning pending |
| Read-only devices | Simulator implemented; physical control excluded |
| Authenticated callbacks/retries | Implemented; HTTP mocked integration passes; actual nginx-qa qualification pending |
| Existing inbound regression | Existing health test plus booking tests run together with bridge tests |
| HUB-10 signed plugin discovery | Implemented with separate HMAC trust key; production signing infrastructure pending |
| HUB-11 installation/activation | Compatible manifest/consent flow simulated; platform package delivery pending |
| HUB-12 capability broker | Implemented and tested: scope, assurance, freshness, expiry and revocation |
| HUB-13 negative security cases | Tests cover forged signatures/QR, replay, cross-project, stale grants and proof lockout |
| HUB-14 microscope end-to-end | Completed against read-only simulator, not hardware |
| HUB-15 smart-card login | Trusted identity assertion simulator, single tap; real reader/IdP adapter pending |
| HUB-16 session assurance | Implemented; tests cover step-up, idle/absolute expiry, revoke and user switch |

See `../../channel_bridge/README.md` for trust boundaries, setup and hardware qualification list,
and `../../channel_bridge/VALIDATION.md` for actual command output. Original unchecked tasks remain
unchanged because simulator coverage does not complete native/platform or cross-repo acceptance.

# Development tasks — inbound-hub
- [ ] Survey existing inbound adapters, FastAPI boundary and persistence conventions.
- [ ] Review and freeze shared wire schemas with nginx-qa.
- [ ] Add independently versioned channel registry and capability/policy model.
- [ ] Implement authenticated request intake and durable dispatch outbox.
- [ ] Implement mobile human status and async messaging simulator with Offline rule.
- [ ] Add QR checkpoint lookup, consented observation metadata and artifact refs.
- [ ] Implement read-only device simulator adapter; no physical control.
- [ ] Post authenticated correlated outcome events to nginx-qa, retries/dedupe.
- [ ] Test existing inbound proposal path unchanged and cross-repo integration.
Done: Hub handles human/device simulation with traceable responses; no production deployment.


- [ ] HUB-10 Implement trusted QR device lookup with signed/versioned plugin capability manifests and no embedded credentials.
- [ ] HUB-11 Define cross-platform mobile module discovery and consented installation/activation, preserving OS security models.
- [ ] HUB-12 Build scoped capability-grant broker, human/agent policy intersection, step-up PIN-unlock or one-time token proof, expiry and revocation.
- [ ] HUB-13 Reject unapproved plugin, forged QR, replayed challenge, stale grant and cross-project privilege escalation; log audit.
- [ ] HUB-14 Integrate simulated microscope phone module read-only observation with restricted plugin grant and verify end-to-end.

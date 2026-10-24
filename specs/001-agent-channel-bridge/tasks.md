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

# 11 — Unresolved Technical Questions

Track open questions before and during implementation. Update this doc as answers arrive.

---

## Priority Matrix

| # | Question | Impact | Status | Resolution Path |
|---|----------|--------|--------|-----------------|
| 1 | Per-user data isolation | Critical | Open | MVP: shared demo; Phase 2: tenant_id |
| 2 | MongoDB from Cloud Agent Executa | Critical | Open | Test connectivity; use developer credential |
| 3 | record_payment confirmation in Anna | High | Open | Two-phase Executa + APS drafts |
| 4 | APS vs MongoDB for pending writes | High | Designed | APS for drafts, MongoDB for business data |
| 5 | Vector search without Gemini key | Medium | Open | Anna llm.embed or regex-only MVP |
| 6 | Qualified MAU measurement | Medium | Open | Ensure tools return meaningful data |
| 7 | Formal Terms vs Jiao email | Medium | Open | Read developer-terms.md before production |
| 8 | External DB in App Review | Medium | Open | Disclose synthetic demo in submission |
| 9 | Cloud Agent 90-day reclamation | Low | Understood | Business data in MongoDB, not workspace |
| 10 | Bilingual in Anna Agent | Low | Designed | system_prompt_addendum + language param |

---

## Q1 — Per-User Data Isolation

**Problem:** Wargio has no `warung_id` or `user_id` on business documents. All users share one database.

**Options:**

| Option | Pros | Cons |
|--------|------|------|
| Shared demo (MVP) | Fast, simple | Not production-ready |
| tenant_id field | Scalable | Requires query changes everywhere |
| DB per user | Strong isolation | Ops overhead |

**Decision for MVP:** Shared synthetic demo DB.  
**Decision for production:** `tenant_id` = Anna user ID on all collections.

---

## Q2 — MongoDB Connectivity from Cloud Agent

**Problem:** Executa runs on Anna Cloud Agent. Can it reach external MongoDB Atlas?

**Considerations:**

- Atlas IP allowlist may block Cloud Agent egress IPs
- Connection string in Executa developer credential (valid pattern per Anna docs)
- Connection pooling across invoke calls (long-running Executa process)

**Action items:**

- [ ] Test `MONGODB_URI` from local `anna-app dev` Executa
- [ ] Test from Anna Cloud Agent after publish
- [ ] Configure Atlas allowlist for Anna egress OR use `0.0.0.0/0` on demo cluster only
- [ ] Document latency observed

---

## Q3 — record_payment Confirmation Flow

**Problem:** Wargio requires ya/batal before DB write. Anna Agent is conversational.

**Proposed solution:**

```text
prepare ? Agent shows summary ? user confirms ? confirm
```

**Open sub-questions:**

- Should Agent call `prepare` automatically or should user explicitly ask?
- How to handle "batal" — new `action=cancel` or just don't call confirm?
- Draft collision if user starts two payments?

**Mitigation:** `system_prompt_addendum` explicitly instructs confirmation flow.

---

## Q4 — APS Draft Storage Implementation

**Problem:** Executa must reverse-RPC to APS for draft storage (protocol v2).

**Requirements:**

- v2 negotiation in `initialize`
- `host_capabilities: ["storage"]` in manifest
- User grants storage for Executa in Anna Admin

**Action items:**

- [ ] Implement v2 capability negotiation in wargio_plugin.py
- [ ] Test APS in `anna-app dev --storage aps` (if supported)
- [ ] Handle `STORAGE_NOT_GRANTED` gracefully

---

## Q5 — Product Fuzzy Matching Without Gemini

**Problem:** `fuzzy_produk.py` uses vector search with Gemini embeddings (768d).

**Options for MVP:**

| Option | Tradeoff |
|--------|----------|
| Regex + partial match only | Simpler, may miss typos |
| Anna `llm.embed` reverse-RPC | No Gemini key, adds latency |
| Pre-computed embeddings in demo DB | Keep existing seed embeddings |
| Skip vector tier | Accept lower match quality |

**MVP recommendation:** Use pre-seeded embeddings in demo DB if available; fallback to exact + partial match only.

---

## Q6 — Qualified MAU Definition

**Problem:** Grant tiers depend on Qualified MAU, not raw opens.

**Hypothesis for Wargio:** Recurring business checks (inventory, sales, debt) naturally drive MAU if app is useful.

**Action items:**

- [ ] Clarify with Anna program docs / Jiao what counts as "meaningful successful app run"
- [ ] Instrument tools to return substantive responses
- [ ] Avoid thin wrapper tools that return empty data

---

## Q7 — Formal Terms vs Jiao Email

**Problem:** IP/ownership assurances from Jiao email, not yet verified against formal agreement.

**Action before production data:**

- [ ] Read `/developers/reference/developer-terms.md`
- [ ] Read Founding Builder Program rules forum post
- [ ] Confirm no exclusivity / ownership transfer clauses conflict

---

## Q8 — External Database in App Review

**Problem:** Anna may scrutinize apps connecting to external databases.

**Mitigation:**

- Synthetic demo data only
- Privacy policy stating external DB usage
- No real PII in MVP
- Document data retention/deletion for demo DB

---

## Q9 — OmniBridge Hardware (Separate Project)

**Problem:** OmniBridge needs local USB/serial. Anna Cloud Agent may not support this.

**Status:** Jiao checking with Anna engineering.

**Decision:** Do NOT start OmniBridge port until architecture confirmed.

See [12-omnibridge-notes.md](12-omnibridge-notes.md).

---

## Q10 — Anna Agent Tool Selection Accuracy

**Problem:** Wargio regex classifier is deterministic. Anna Agent may call wrong tool.

**Mitigations:**

- Clear tool descriptions in Executa manifest
- Strong `system_prompt_addendum`
- Example queries in tool descriptions
- Test common Indonesian phrasings in fixtures

**Action items:**

- [ ] Build fixture set of 20+ common warung queries
- [ ] Measure tool selection accuracy in `anna-app dev`
- [ ] Iterate prompt + descriptions based on failures

---

## Decision Log

| Date | Question | Decision | Rationale |
|------|----------|----------|-----------|
| 2026-08-15 | Architecture approach | Executa wrapper, not /api/chat proxy | Anna-native tool model |
| 2026-08-15 | MVP tools | 4 tools only | Vertical slice first |
| 2026-08-15 | Demo DB | Separate wargio_anna_demo | No production data |
| 2026-08-15 | OmniBridge | Deferred | Hardware access unresolved |

*Add rows as decisions are made during implementation.*

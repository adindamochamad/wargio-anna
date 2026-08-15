# 10 — Security & Data Policy

---

## 10.1 Rules (Non-Negotiable for MVP)

1. **No production data** in Anna Edition development or beta
2. **No production credentials** in repo, manifest, or Executa bundle
3. **Separate demo database** — `wargio_anna_demo`, not `wargio_demo`
4. **Synthetic seed data only** until Anna data/security model fully understood
5. **Review formal Terms** before handling real business data

---

## 10.2 Wargio Original Security Posture

| Issue | Severity | Anna Edition Mitigation |
|-------|----------|-------------------------|
| No authentication | High | Anna signed-in user identity |
| Single shared database | High | Demo DB for beta; `tenant_id` Phase 2 |
| Client-controlled session UUID | Medium | Anna session replaces X-Session-Id |
| PII in customers collection | Medium | Synthetic demo data without real PII |
| Public /api/health | Low | No HTTP health endpoint in Executa |
| MONGODB_URI in .env | High | Executa developer credential, not in iframe |

---

## 10.3 Credential Handling

### Wargio Original

```
MONGODB_URI ? .env on VPS (never commit)
GEMINI_API_KEY ? .env (Anna Edition may not need for MVP)
```

### Anna Edition

| Secret | Where | Who sees it |
|--------|-------|-------------|
| `MONGODB_URI` (demo) | Executa developer credential | Executa process only |
| Gemini key (if embeddings) | Executa credential OR use `llm.embed` | Executa / Anna host |
| Anna PAT | `~/.config/anna/credentials.json` | Local dev CLI only |

**Never expose secrets in:**

- `manifest.json`
- `bundle/` (iframe — browser inspectable)
- Git repository
- App Review screenshots

---

## 10.4 Data Storage Tiers

| Tier | Technology | Data | Retention |
|------|------------|------|-----------|
| Authoritative business | MongoDB Atlas (demo) | products, customers, transactions | Until manual reset |
| Ephemeral drafts | APS (`scope: tool`) | payment confirmation drafts | TTL 30 min |
| User preferences | APS (`scope: app`) | language | Until user uninstalls |
| Workspace | `$ANNA_WORKSPACE_DIR` | temp files only | 90-day reclamation on idle Cloud Agent |
| Conversation | Anna platform | chat history | Anna policy |

---

## 10.5 Multi-Tenant Isolation (Phase 2 — Post Beta)

Wargio original has **no tenant model**. Before public launch with real warung data:

### Option A — Field-level isolation

Add `tenant_id` (Anna user ID) to all business documents:

```javascript
// products, customers, transactions
{ tenant_id: "anna_user_123", ... }
```

All queries filter by `tenant_id`.

### Option B — Database-per-tenant

Separate MongoDB database per user — expensive, complex.

### Option C — Shared demo only

Keep shared synthetic demo for App Store; real users get isolated tenant on signup.

**MVP:** Option C (shared demo). Phase 2: Option A.

---

## 10.6 Data Lifecycle

| Operation | MVP | Production (future) |
|-----------|-----|---------------------|
| Create | Seed script | User onboarding |
| Read | Executa tools | Executa tools + tenant filter |
| Update | record_payment confirm | Same + audit log |
| Delete | Manual DB reset | User data deletion API |
| Export | Not in MVP | APS files or export tool |
| Backup | Atlas backup on demo cluster | Per-tenant backup policy |

---

## 10.7 Write Safety (Preserved from Wargio)

| Mechanism | Wargio Original | Anna Edition |
|-----------|-----------------|--------------|
| Confirmation before write | ya/batal in chat | prepare/confirm two-phase |
| Draft expiry | 30 min (`konfirmasi.py`) | APS TTL 1800s |
| Atomic transactions | `transaksi_atomik.py` | Same |
| Stock race check | `StokKonfirmasiGagal` | Same |
| Disambiguation | Multi-turn in session | Agent multi-turn |

---

## 10.8 App Review Disclosure

Include in privacy policy / review notes:

- App uses **synthetic demo business data** for initial release
- External MongoDB Atlas connection (developer-managed demo cluster)
- No real customer PII collected by Anna Edition in MVP
- Payment recording modifies demo database only
- Data retention: demo DB reset periodically during beta

---

## 10.9 Qualified MAU Implications

Qualified MAU requires **meaningful successful app run**. For Wargio:

| Counts as meaningful | Does NOT count |
|---------------------|----------------|
| Successful get_inventory with real data returned | App open with no tool call |
| get_sales returning revenue figure | Failed tool call |
| record_payment completed after confirm | prepare-only without follow-up |
| get_debts listing debtors | Agent hallucinating without tool |

Design tools to return **structured, verifiable business data** — not empty acknowledgments.

---

## 10.10 IP / Ownership Reminder

Per Jiao (verify against formal Terms):

- Wargio IP remains with developer
- Anna Edition does not transfer ownership
- No exclusivity — continue independent Wargio distribution
- OmniBridge same treatment when started later

Formal reference: `/developers/reference/developer-terms.md`

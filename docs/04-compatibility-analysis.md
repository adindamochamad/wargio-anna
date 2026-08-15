# 04 — Compatibility Analysis: Wargio ? Anna

---

## 4.1 Compatibility Map

| Existing Wargio | Possible Anna Equivalent | Verdict |
|-----------------|--------------------------|---------|
| Next.js UI | Anna App UI bundle (schema: 2) | **Adapt** |
| FastAPI `/api/chat` | Anna Agent + Executa tools | **Replace runtime** |
| Gemini classification | Anna Agent LLM | **Replace** |
| Intent handlers | Executa `invoke` internals | **Reuse** |
| `atlas_tools` + PyMongo | Executa + developer credential | **Reuse** |
| ADK Agent Engine | — | **Skip** |
| MongoDB `agent_sessions` | APS KV + Anna conversation | **Adapt** |
| Auth (none) | Anna identity | **Replace** (enables isolation) |
| Dashboard SSR | Anna UI + `tools.invoke` | **Adapt** |
| Business logic modules | Executa internals | **Reuse** |
| Gemini embeddings | `llm.embed` or keep in Executa | **Evaluate** |
| Docker VPS deploy | Anna Cloud Agent | **Replace for Anna Edition** |
| Rate limiting | Anna platform quota | **Replace** |
| i18n ID/EN | `system_prompt_addendum` + tool params | **Adapt** |

**Do not assume mappings correct until verified against Anna docs at implementation time.**

---

## 4.2 Reuse Directly

| Module | Path in Wargio | Anna Role |
|--------|----------------|-----------|
| Read handlers | `intent_handlers.py` | Executa tool backends |
| Write handlers | `write_handlers.py` | `record_payment` backend |
| MongoDB layer | `atlas_tools.py` | Executa data access |
| Product resolution | `fuzzy_produk.py`, `produk.py` | Executa internals |
| Entity extraction | `ekstrak_entitas.py` | Payment/sale parsing |
| Confirmation logic | `konfirmasi.py` | Adapt to APS-backed drafts |
| Atomic writes | `transaksi_atomik.py` | Payment execution safety |
| Formatting | `util/format.py`, `util/lokalisasi.py` | Response formatting |
| DB connection | `db/koneksi.py` | Executa MongoDB pool |
| Seed data | `scripts/seed_data.py` | Demo DB for Anna Edition |

---

## 4.3 Must Adapt

| Component | From | To |
|-----------|------|-----|
| Runtime entry | FastAPI chat route | Executa stdio JSON-RPC |
| NL routing | Gemini + regex classifier | Anna Agent tool selection |
| Session state | MongoDB `agent_sessions` | APS + Anna conversation |
| Multi-tenancy | None | `tenant_id` scoped to Anna user (Phase 2) |
| Frontend | Next.js | Anna App UI bundle |
| Credentials | `.env` on VPS | Executa developer credential |
| Confirmation UX | ya/batal in chat session | Two-phase Executa or Agent multi-turn |

---

## 4.4 Must Rewrite

| Component | Reason |
|-----------|--------|
| `executor.py` | Anna Agent replaces orchestration |
| `agent_gemini.py` | Anna Agent replaces classification |
| `sesi.py` | Anna manages conversation history |
| FastAPI app + routes | Not deployed in Anna Edition MVP |
| Next.js frontend | Replaced by Anna UI bundle |
| Docker/Nginx deploy | Anna hosts Executa runtime |
| ADK agent (`agent/wargio/`) | Redundant with Anna Agent |

---

## 4.5 Should Become Executa

**Single plugin: `wargio-executa`**

| Anna Tool | Wargio Source | MVP? |
|-----------|---------------|------|
| `get_inventory` | `handle_check_stock` + `handle_restock_alert` | ? |
| `get_sales` | `handle_sales_report` | ? |
| `get_debts` | `handle_check_debt` + `handle_debt_collection` | ? |
| `record_payment` | `siapkan_record_payment` + `eksekusi_record_payment` | ? |
| `record_sale` | write_handlers | Phase 2 |
| `sales_forecast` | `handle_sales_forecast` | Phase 2 |

---

## 4.6 Should Become Anna UI

Minimal schema: 2 bundle:

- 3 dashboard cards (stok kritis, hutang terbesar, omzet hari ini)
- Quick-action chips
- Primary interaction via `#wargio` in Anna chat (not custom chat widget)

Source reference: `frontend/src/components/dashboard/ringkasan-dashboard.tsx`, `aksi-cepat.tsx`

---

## 4.7 Should Use Anna Host APIs

| API | Wargio Anna Use |
|-----|-----------------|
| `tools.invoke` | UI dashboard refresh |
| `storage.*` | Pending payment drafts, language pref |
| `llm.embed` | Optional — replace Gemini embeddings |
| `chat.write_message` | Optional — post structured summaries |

**Do NOT use `llm.complete` in Executa for business answers** — handlers already return formatted data.

---

## 4.8 Should Remain External

| System | Reason |
|--------|--------|
| MongoDB Atlas | Document model, aggregations, transactions, vector search too rich for APS alone |
| Original Wargio deploy | Independent product at wargio.adindamochamad.com |
| Gemini API key | Only if keeping embeddings outside Anna; classification key unnecessary |

---

## 4.9 Anti-Patterns to Avoid

| Anti-pattern | Why |
|--------------|-----|
| Proxy `/api/chat` to Anna | Wrong layer — couples HTTP chat to Anna tool model |
| Rewrite all business logic | Unnecessary — handlers are the asset |
| Put business data in APS KV | Wrong storage tier |
| Import OpenAI in Executa for NL | Bypasses user quota/model choice |
| Port all 8 intents before first vertical slice | Delays feasibility proof |
| Use production MongoDB in beta | Security/compliance unknown |
| Start OmniBridge now | Hardware access unresolved |

---

## 4.10 Anna Agent vs Wargio Intent Engine

| Wargio Today | Anna Edition |
|--------------|--------------|
| User message ? Gemini classify ? regex override | User message ? Anna Agent reasons |
| Fixed 8-intent router | Agent selects from Executa tool manifest |
| Templated handler responses | Same templated responses from Executa `data` |
| Session pending write in MongoDB | APS draft + Agent confirmation turn |
| `X-Wargio-Language` header | `language` param or Agent detects from message |

**Advantage:** Anna Agent handles ambiguous NL better than regex.  
**Risk:** Agent may call wrong tool — mitigate with clear tool descriptions + `system_prompt_addendum`.

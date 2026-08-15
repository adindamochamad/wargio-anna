# 09 — Vendor Map: Wargio Files to Reuse

Mapping file dari repo Wargio asli (`/Users/mac/Development/wargio`) ke `executas/wargio/wargio_core/`.

---

## 9.1 Copy — Business Logic (Required)

| Source (Wargio) | Target (wargio-anna) | Purpose |
|-----------------|----------------------|---------|
| `backend/app/services/intent_handlers.py` | `wargio_core/services/intent_handlers.py` | Read handlers |
| `backend/app/services/write_handlers.py` | `wargio_core/services/write_handlers.py` | Payment write |
| `backend/app/services/atlas_tools.py` | `wargio_core/services/atlas_tools.py` | MongoDB ops |
| `backend/app/services/fuzzy_produk.py` | `wargio_core/services/fuzzy_produk.py` | Product resolution |
| `backend/app/services/produk.py` | `wargio_core/services/produk.py` | Product search wrapper |
| `backend/app/services/ekstrak_entitas.py` | `wargio_core/services/ekstrak_entitas.py` | NL entity extraction |
| `backend/app/services/konfirmasi.py` | `wargio_core/services/konfirmasi.py` | Confirmation helpers (adapt for APS) |
| `backend/app/services/disambiguasi.py` | `wargio_core/services/disambiguasi.py` | Disambiguation |
| `backend/app/services/transaksi_atomik.py` | `wargio_core/services/transaksi_atomik.py` | Atomic writes |
| `backend/app/services/klasifikasi.py` | `wargio_core/services/klasifikasi.py` | Entity extract helpers only (`ekstrak_nama_produk`, etc.) — NOT full intent routing |
| `backend/app/db/koneksi.py` | `wargio_core/db/koneksi.py` | AsyncMongoClient |
| `backend/app/util/format.py` | `wargio_core/util/format.py` | Rupiah, dates |
| `backend/app/util/lokalisasi.py` | `wargio_core/util/lokalisasi.py` | ID/EN strings |

---

## 9.2 Copy — Conditional (MVP may skip)

| Source | Condition | Purpose |
|--------|-----------|---------|
| `backend/app/services/embed_produk.py` | If vector search needed | Gemini embeddings |
| `backend/app/services/agent_gemini.py` | ? Skip MVP | Classification replaced by Anna Agent |
| `backend/app/services/mcp_klien.py` | ? Skip | MCP verify not needed in Executa |
| `backend/app/schemas/chat.py` | Partial | Types if needed |
| `backend/app/schemas/dashboard.py` | Optional | UI response shapes |

---

## 9.3 Do NOT Copy

| Source | Reason |
|--------|--------|
| `backend/app/main.py` | FastAPI not used |
| `backend/app/api/routes/*` | HTTP routes replaced by Executa |
| `backend/app/services/executor.py` | Anna Agent replaces |
| `backend/app/services/agent_gemini.py` | Anna Agent replaces |
| `backend/app/services/sesi.py` | Anna manages conversation |
| `backend/app/services/dashboard.py` | UI calls tools directly (or thin adapter) |
| `backend/app/middleware/rate_limit.py` | Anna handles quota |
| `backend/app/config.py` | New minimal config for Executa |
| `frontend/**` | Replaced by Anna UI bundle |
| `agent/wargio/**` | ADK path not needed |
| `deploy/**` | Anna hosts runtime |

---

## 9.4 Scripts to Adapt

| Script | Purpose for Anna Edition |
|--------|--------------------------|
| `scripts/seed_data.py` | Seed `wargio_anna_demo` |
| `scripts/buat_indeks.py` | Create indexes on demo DB |
| `scripts/products_vector_index.json` | Vector index (Phase 2) |
| `scripts/isi_embedding_produk.py` | Embeddings (Phase 2) |

Run against **separate demo database**, not `wargio_demo` production.

---

## 9.5 Import Adaptation Notes

Wargio uses `from app.services...` imports. After vendoring to `wargio_core/`:

**Option A — Rename imports:**

```python
from wargio_core.services.intent_handlers import handle_check_stock
```

**Option B — Keep `app` namespace:**

Copy to `wargio_core/app/` preserving structure, add to PYTHONPATH.

**Recommended:** Option A for clarity in Anna Edition.

### Dependencies to add in `executas/wargio/pyproject.toml`

```toml
dependencies = [
  "pymongo>=4.0",
  # embed_produk only if needed:
  # "google-genai>=1.0",
]
```

Remove: fastapi, uvicorn, google-adk, mcp (unless needed).

---

## 9.6 Files Requiring Modification After Copy

| File | Modification |
|------|--------------|
| `konfirmasi.py` | APS-backed pending state instead of MongoDB session |
| `koneksi.py` | Read `MONGODB_URI` from Executa credential/env |
| `lokalisasi.py` | Set language from tool param instead of HTTP header |
| `atlas_tools.py` | Disable MCP live path (`MCP_LIVE_ENABLED` always false) |
| `write_handlers.py` | Accept explicit params, not only parsed from `pesan` |

---

## 9.7 New Files to Create

| File | Purpose |
|------|---------|
| `executas/wargio/wargio_plugin.py` | Executa stdio server |
| `executas/wargio/pyproject.toml` | Python deps |
| `executas/wargio/adapters/inventory.py` | Map get_inventory ? handlers |
| `executas/wargio/adapters/sales.py` | Map get_sales ? handlers |
| `executas/wargio/adapters/debts.py` | Map get_debts ? handlers |
| `executas/wargio/adapters/payment.py` | Map record_payment ? handlers + APS |
| `executas/wargio/adapters/aps_draft.py` | APS draft storage for confirmations |
| `manifest.json` | Anna App manifest |
| `app.json` | Listing metadata |
| `bundle/*` | UI SPA |

---

## 9.8 Dependency Graph (Copied Modules)

```text
wargio_plugin.py
  ??? adapters/
        ??? inventory.py ? intent_handlers (check_stock, restock_alert)
        ??? sales.py ? intent_handlers (sales_report)
        ??? debts.py ? intent_handlers (check_debt, debt_collection)
        ??? payment.py ? write_handlers + aps_draft
              ??? wargio_core/services/*
                    ??? atlas_tools ? db/koneksi
                    ??? fuzzy_produk ? produk ? embed_produk (optional)
                    ??? ekstrak_entitas
                    ??? konfirmasi (adapted)
                    ??? transaksi_atomik
                    ??? util/format, util/lokalisasi
```

---

## 9.9 Sync Strategy with Upstream Wargio

To keep original Wargio independent:

1. **Manual sync** — periodically copy changed handler files
2. **Git submodule** — `wargio/backend/app` as submodule (more complex imports)
3. **Shared package** — extract `wargio-core` PyPI package later (post-MVP)

**MVP recommendation:** Manual copy with documented diff. Re-sync after Wargio bugfixes to handlers.

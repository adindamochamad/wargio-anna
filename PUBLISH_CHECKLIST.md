# Wargio Anna Edition — Publish Checklist

> Generated: 2026-08-15  
> App slug: `wargio-anna` | App ID: 180 | Status: **DRAFT**  
> Executa: `tool-dev-wargio` (registered locally, **not yet published to server**)

---

## ✅ What's Been Completed

| Item | Evidence |
|------|----------|
| `manifest.json` created | Schema 2, permissions, system_prompt, UI config |
| `app.json` metadata | Name, tagline, description, category, pricing_model |
| App registered on server | `.anna/dev-app.json` → app_id: 180, slug: `wargio-anna` |
| Executa plugin code | `executas/wargio/wargio_plugin.py` with 4 tools |
| Executa registered locally | `.anna/dev-executa.json` → tool_id: `tool-dev-wargio` |
| UI bundle | `bundle/index.html`, `bundle/app.js`, `bundle/styles.css` |
| Icon asset | `assets/logo.svg` |
| Fixtures (tool test data) | `fixtures/tools.jsonl` |
| Validation passes | `anna-app validate` ✓ (basic) |
| Validation passes (strict) | `anna-app validate --strict` ✓ |
| Seed data script | `scripts/seed_data.py` |
| Smoke test script | `scripts/smoke_test_executa.py` |

---

## ❌ What's Still Needed Before Publish

### Critical (blocks publish)

| # | Issue | Fix |
|---|-------|-----|
| 1 | **`app.json` missing `slug` field** | Add `"slug": "wargio-anna"` to `app.json`. The `anna-app publish` / `apps publish` command fails with: `✗ app.json missing required 'slug' (3-80 chars, kebab-case)` |
| 2 | **Executa not published to server** | `anna-app executa list` shows no `tool-dev-wargio`. Must publish executa before the app can reference it. |
| 3 | **`required_executas` tool_id mismatch** | After real executa publish, manifest's `required_executas[0].tool_id` must match the server-assigned tool_id (may differ from dev `tool-dev-wargio`). |

### Recommended (before submit-review)

| # | Item | Notes |
|---|------|-------|
| 4 | Replace placeholder URLs | `privacy_url` and `support_url` in `app.json` point to `wargio.example.com` — must be real URLs for review. |
| 5 | Screenshots for store listing | `assets/screenshots.md` exists but actual screenshot images are not present in `assets/`. |
| 6 | Run smoke test end-to-end | `python scripts/smoke_test_executa.py` — confirm all 4 tools respond correctly with fixtures. |
| 7 | Version number | `pyproject.toml` shows `0.1.0`. Decide on release version. Manifest has no explicit version (server assigns). |
| 8 | Remove `.env` from tracked files | `.env` exists in project root (should be gitignored, confirm no secrets leak). |

---

## 📋 Publish Workflow (Commands)

The full lifecycle from draft → live:

```bash
# ─── Step 0: Pre-flight validation ───
anna-app validate                    # Basic schema + ACL check
anna-app validate --strict           # Strict mode (host_api ACL grep)

# ─── Step 1: Fix app.json slug ───
# Add "slug": "wargio-anna" to app.json

# ─── Step 2: Publish Executa first ───
cd executas/wargio
anna-app executa publish             # Mints/updates executa on server
anna-app executa publish --publish   # + flips visibility to PUBLIC
cd ../..

# ─── Step 3: Update manifest.json tool_id ───
# Replace "tool-dev-wargio" with server-assigned tool_id from step 2
# (or use --executa-id flag in step 4)

# ─── Step 4: Push working draft (App) ───
anna-app apps push                   # Uploads manifest + bundle as mutable draft
# OR with executa override:
anna-app apps push --executa-id "tool-dev-wargio=<real-tool-id>"

# ─── Step 5: Validate on server (dry-run publish) ───
anna-app apps publish --dry-run      # Resolve identity + diff, no upload

# ─── Step 6: Cut an immutable version ───
anna-app apps cut 1.0.0 --changelog "Initial release: inventory, sales, debts, payments"

# ─── Step 7: Submit for review ───
anna-app apps submit-review wargio-anna   # DRAFT → PENDING_REVIEW

# ─── Step 8: (After approval) Release ───
anna-app apps release 1.0.0          # Freeze & publish (go live)
```

### Quick publish (all-in-one shortcut)

```bash
# This auto-detects cwd and runs apps publish OR executa publish:
anna-app publish --bump patch        # But requires app.json slug fix first
```

### Dry-run (safe to run anytime)

```bash
anna-app publish --dry-run           # See what would happen without uploading
anna-app apps push --dry-run         # Draft push dry-run
anna-app apps publish --dry-run      # Full publish dry-run
```

---

## 🔍 Useful Status Commands

```bash
anna-app apps status wargio-anna     # Server state for the app
anna-app apps versions wargio-anna   # List immutable versions
anna-app apps grants wargio-anna     # Check granted scopes/quota
anna-app apps list                   # All your apps
anna-app executa list                # All your executas
anna-app executa status <ref>        # Server state for executa
```

---

## ⚠️ Known Limitations

1. **Data is synthetic only** — `fixtures/tools.jsonl` and `scripts/seed_data.py` use demo data. Production MongoDB not connected.
2. **Executa is Python (local distribution)** — requires Anna platform to support Python executa runtime, or must be hosted externally.
3. **Privacy/Support URLs are placeholders** — will be flagged during review.
4. **No automated CI/CD** — publish steps are manual CLI commands.
5. **Single executa bundles 4 tools** — `get_inventory`, `get_sales`, `get_debts`, `record_payment` all in one plugin. If Anna review prefers separate executas, refactoring is needed.
6. **No `executa.json` manifest** — the executa folder has `pyproject.toml` but no `executa.json`. The `anna-app executa publish` command expects `executa.json` in cwd (see `--manifest` option). This may need to be created.

---

## 📁 Project Structure Reference

```
wargio-anna/
├── manifest.json          ← App manifest (schema 2)
├── app.json               ← Store metadata (NEEDS slug field)
├── .anna/dev-app.json     ← Server registration cache
├── bundle/                ← Static SPA UI
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── assets/
│   ├── logo.svg           ← App icon
│   └── screenshots.md     ← Screenshot list (images TBD)
├── executas/wargio/       ← Executa plugin
│   ├── wargio_plugin.py   ← Entry point (4 tools)
│   ├── pyproject.toml     ← Python package config
│   ├── adapters/          ← Tool implementations
│   ├── wargio_core/       ← Business logic (reused from Wargio)
│   └── .anna/dev-executa.json  ← Executa registration cache
├── fixtures/tools.jsonl   ← Test fixtures
├── scripts/
│   ├── seed_data.py       ← Seed demo MongoDB
│   └── smoke_test_executa.py  ← Local smoke test
└── docs/                  ← Architecture & planning docs
```

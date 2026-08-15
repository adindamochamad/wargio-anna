# 06 — Migration Plan: Wargio ? Wargio Anna Edition

---

## 6.1 Strategy

```text
Phase 0  Understand Anna Hello World
    ?
Phase 1  Minimal Anna App scaffold
    ?
Phase 2  First Executa tool (get_inventory)
    ?
Phase 3  Connect Agent ? Executa ? data ? response
    ?
Phase 4  Remaining MVP read tools
    ?
Phase 5  record_payment write tool
    ?
Phase 6  Minimal production UI
    ?
Phase 7  Submit App Review (early)
    ?
Phase 8  Beta 5–20 users
    ?
Phase 9  Iterate ? 200 Qualified MAU
```

---

## Phase 0 — Anna Hello World (1–2 days)

**Goal:** Working dev toolchain.

```bash
fnm install 22 && fnm default 22
curl -LsSf https://astral.sh/uv/install.sh | sh
npm install -g @anna-ai/cli
anna-app doctor
anna-app login --host https://anna.partners
```

- Set Local Agent as default in Anna UI
- Read Build on Anna 101 end-to-end
- Run `anna-app init` smoke test in temp dir

**Deliverable:** `anna-app doctor` green, PAT saved.

---

## Phase 1 — Scaffold wargio-anna (2–3 days)

```bash
anna-app init wargio-anna --slug wargio
cd wargio-anna
anna-app dev   # verify ping/pong at localhost:5180
```

- Create folder structure per [05-target-architecture.md](05-target-architecture.md)
- Draft `manifest.json`, `app.json`
- Stub Executa with ping tool
- Stub UI with placeholder cards

**Deliverable:** Harness runs, validate passes (non-strict).

---

## Phase 2 — Vertical Slice: get_inventory (3–5 days)

1. Vendor `wargio_core/` per [09-vendor-map.md](09-vendor-map.md)
2. Implement `wargio_plugin.py` long-running stdio loop
3. Wire `get_inventory` ? `handle_check_stock` + `handle_restock_alert`
4. Connect demo MongoDB (`wargio_anna_demo`)
5. Update `system_prompt_addendum`
6. Test:

```text
#wargio "Produk apa yang hampir habis?"
#wargio "Berapa stok Indomie?"
```

**Deliverable:** End-to-end read path works.

**Success criterion:**

```text
Anna App ? User asks Wargio question ? Agent ? Executa ? MongoDB ? useful answer
```

---

## Phase 3 — Remaining Read Tools (3–4 days, parallel possible)

| Tool | Handler | Test query |
|------|---------|------------|
| `get_sales` | `handle_sales_report` | "Berapa penjualan minggu ini?" |
| `get_debts` | `handle_check_debt`, `handle_debt_collection` | "Siapa yang masih punya hutang?" |

Add fixtures in `fixtures/demo_scenarios.jsonl`.

**Deliverable:** 3 read tools stable.

---

## Phase 4 — Write Tool: record_payment (3–5 days, sequential)

1. Design two-phase API: `prepare` / `confirm`
2. Store drafts in APS via reverse-RPC `storage/set`
3. Wrap `siapkan_record_payment` + `eksekusi_record_payment`
4. Test multi-turn:

```text
"Catat pembayaran Budi 50000" ? summary ? "Ya" ? confirmed write
"Batal" ? draft cleared
```

**Deliverable:** Safe write path with confirmation.

---

## Phase 5 — Minimal UI (3–5 days)

Port from Wargio frontend:

- Card: stok kritis (restock_alert)
- Card: hutang terbesar (debt query)
- Card: omzet hari ini (sales today)
- Quick actions: chips ? `tools.invoke`

Run `anna-app validate --strict`.

**Deliverable:** Functional dashboard UI.

---

## Phase 6 — Publish & Review (3–5 days)

1. Publish Executa ? catalogue `tool_id: wargio`
2. Update manifest to published tool_id
3. Prepare listing: logo, screenshots, tagline, privacy URL
4. Submit for App Review **early**
5. Iterate on rejection feedback

**Deliverable:** App in PENDING_REVIEW or PUBLISHED.

---

## Phase 7 — Beta (2–4 weeks)

- 5–20 beta users
- Monitor Qualified MAU (meaningful successful runs)
- Fix NL edge cases, response quality
- Publish SemVer updates

---

## Phase 8 — Growth (ongoing)

| Priority | Feature |
|----------|---------|
| P1 | Per-user `tenant_id` isolation |
| P2 | `record_sale` tool |
| P3 | `sales_forecast` |
| P4 | Vector search via `llm.embed` |
| P5 | Data export tool |

---

## 6.2 What NOT to Do

- ? Rewrite Wargio from scratch
- ? Proxy `/api/chat`
- ? Port entire Next.js app
- ? Use production MongoDB
- ? Implement all 8 intents before slice 1
- ? Start OmniBridge
- ? Optimize for 20K MAU before feasibility

---

## 6.3 Engineering Principles (Reminder)

1. Preserve original Wargio functionality
2. Avoid rewriting working business logic
3. Keep Anna integration isolated
4. Prefer adapter/Executa layer
5. No undocumented Anna APIs
6. Synthetic data until security model clear
7. No production credentials in repo
8. Original Wargio independently deployable
9. Smallest complete vertical slice first
10. Submit early for review
11. Anna = new distribution, not replacement

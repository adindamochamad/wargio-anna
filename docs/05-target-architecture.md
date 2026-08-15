# 05 — Target Architecture: Wargio Anna Edition

---

## 5.1 Conceptual Model

```text
                    Anna App (Wargio)
                           ?
              ???????????????????????????
              ?                         ?
         Anna App UI              Anna Agent
      (dashboard cards)         (#wargio mention)
              ?                         ?
              ?    anna.tools.invoke    ?
              ???????????????????????????
                           ?
                           ?
                   Wargio Executa
                  (stdio JSON-RPC)
                           ?
         ?????????????????????????????????????
         ?                 ?                 ?
         ?                 ?                 ?
   get_inventory      get_sales         get_debts
   record_payment     (MVP tools)
         ?                 ?                 ?
         ?????????????????????????????????????
                           ?
                           ?
              Wargio Business Logic Layer
         (intent_handlers, write_handlers,
          fuzzy_produk, atlas_tools)
                           ?
                           ?
              MongoDB Atlas (demo DB)
              wargio_anna_demo
```

**Do NOT rewrite Wargio from scratch.** Anna Edition = adapter/runtime layer around existing domain logic.

---

## 5.2 Invocation Paths

### Path A — Conversational (primary)

```text
User: #wargio "Produk apa yang hampir habis?"
  ? Anna Agent reads system_prompt_addendum
  ? Agent calls get_inventory(query_type="restock_alert")
  ? Executa ? handle_restock_alert ? MongoDB
  ? Returns structured data
  ? Agent formats natural language reply
```

### Path B — Dashboard UI

```text
User opens Wargio App window
  ? UI calls anna.tools.invoke("get_inventory", {...})
  ? Same Executa path
  ? UI renders cards
```

### Path C — Write with confirmation

```text
User: "Catat pembayaran Budi 50000"
  ? Agent calls record_payment(action="prepare", ...)
  ? Executa returns draft summary + draft_id
  ? Agent asks user to confirm
  ? User: "Ya"
  ? Agent calls record_payment(action="confirm", draft_id=...)
  ? Executa ? eksekusi_record_payment ? MongoDB
```

---

## 5.3 Project Structure (Target)

```text
wargio-anna/
??? README.md
??? docs/                          # Context documentation (this folder)
??? manifest.json                  # schema: 2
??? app.json                       # listing metadata
??? bundle/
?   ??? index.html
?   ??? app.js
?   ??? styles.css
??? executas/
?   ??? wargio/
?       ??? wargio_plugin.py       # describe / invoke / health loop
?       ??? pyproject.toml
?       ??? wargio_core/           # vendored from wargio/backend/app/
?           ??? services/
?           ??? db/
?           ??? util/
?           ??? schemas/           # minimal subset
??? fixtures/
?   ??? demo_scenarios.jsonl
??? .env.example                   # MONGODB_URI demo only
```

**Original Wargio repo untouched.** Anna Edition imports services as library copy or git submodule.

---

## 5.4 Executa Tool Manifest (Draft)

```json
{
  "name": "wargio",
  "display_name": "Wargio",
  "version": "0.1.0",
  "description": "AI business assistant for Indonesian warung — inventory, sales, debts, payments.",
  "host_capabilities": ["storage"],
  "tools": [
    {
      "name": "get_inventory",
      "description": "Check product stock or list products needing restock",
      "parameters": [
        { "name": "query_type", "type": "string", "enum": ["check_product", "restock_alert"], "required": true },
        { "name": "product_name", "type": "string", "required": false },
        { "name": "language", "type": "string", "enum": ["id", "en"], "required": false }
      ]
    },
    {
      "name": "get_sales",
      "description": "Get sales revenue report for today or this week",
      "parameters": [
        { "name": "period", "type": "string", "enum": ["today", "week"], "required": false },
        { "name": "language", "type": "string", "enum": ["id", "en"], "required": false }
      ]
    },
    {
      "name": "get_debts",
      "description": "Check customer debt or list all customers with outstanding debt",
      "parameters": [
        { "name": "query_type", "type": "string", "enum": ["check_customer", "list_all"], "required": true },
        { "name": "customer_name", "type": "string", "required": false },
        { "name": "language", "type": "string", "enum": ["id", "en"], "required": false }
      ]
    },
    {
      "name": "record_payment",
      "description": "Prepare or confirm a debt payment recording",
      "parameters": [
        { "name": "action", "type": "string", "enum": ["prepare", "confirm"], "required": true },
        { "name": "customer_name", "type": "string", "required": false },
        { "name": "amount", "type": "number", "required": false },
        { "name": "draft_id", "type": "string", "required": false },
        { "name": "language", "type": "string", "enum": ["id", "en"], "required": false }
      ]
    }
  ]
}
```

---

## 5.5 App Manifest (Draft)

```json
{
  "schema": 2,
  "required_executas": [{ "tool_id": "tool-dev-wargio" }],
  "permissions": ["tools.invoke", "storage.read", "storage.write"],
  "system_prompt_addendum": "You are Wargio, an AI business assistant for Indonesian warung (micro-retail) owners. Help check inventory, sales, debts, and record payments. Respond in the same language the user writes (Bahasa Indonesia or English). Use bundled Wargio tools for ALL business data — never invent numbers. For record_payment, always call prepare first, show summary, wait for explicit user confirmation, then call confirm.",
  "ui": {
    "bundle": { "entry": "index.html" },
    "host_api": {
      "tools": ["invoke"],
      "storage": ["get", "set"]
    }
  }
}
```

Replace `tool-dev-wargio` with published `tool_id` before App Store submission.

---

## 5.6 Data Architecture Decision

| Data Type | Storage | Rationale |
|-----------|---------|-----------|
| Products, customers, transactions | **MongoDB Atlas** (demo DB) | Complex queries, aggregations, transactions |
| Pending payment drafts | **APS** (`scope: tool`) | Ephemeral, per-user, survives Executa restart |
| User language preference | **APS** (`scope: app`) | Small KV |
| Executa working files | **`$ANNA_WORKSPACE_DIR`** | Temp/cache only |
| Chat history | **Anna platform** | Not stored in Wargio |

### Demo DB

- Database name: `wargio_anna_demo` (separate from `wargio_demo` production)
- Seed via adapted `scripts/seed_data.py`
- No real customer PII

---

## 5.7 What Stays in Original Wargio

| Component | Continues independently |
|-----------|------------------------|
| VPS deploy at wargio.adindamochamad.com | ? |
| FastAPI + Next.js stack | ? |
| Gemini classification path | ? |
| GitHub releases | ? |
| Hackathon/ADK Agent Engine artifact | ? |

Anna Edition = **new distribution channel**, not replacement.

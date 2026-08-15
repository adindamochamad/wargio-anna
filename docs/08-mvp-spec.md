# 08 — MVP Specification

Scope: **4 Executa tools** — smallest complete vertical slice proving Anna integration.

---

## 8.1 MVP Tools Overview

| Tool | Type | Wargio Intent(s) | Example Query (ID) |
|------|------|------------------|-------------------|
| `get_inventory` | Read | `check_stock`, `restock_alert` | "Produk apa yang hampir habis?" |
| `get_sales` | Read | `sales_report` | "Berapa penjualan minggu ini?" |
| `get_debts` | Read | `check_debt`, `debt_collection` | "Siapa yang masih punya hutang?" |
| `record_payment` | Write | `record_payment` | "Catat pembayaran Budi Rp50.000" |

**NOT in MVP:** `record_sale`, `sales_forecast`, dashboard SSR, full chat UI, vector search.

---

## 8.2 Tool: get_inventory

### Parameters

| Name | Type | Required | Values |
|------|------|----------|--------|
| `query_type` | string | yes | `check_product`, `restock_alert` |
| `product_name` | string | no | Required when `query_type=check_product` |
| `language` | string | no | `id` (default), `en` |

### Handler Mapping

| query_type | Wargio Handler | Source |
|------------|----------------|--------|
| `check_product` | `handle_check_stock` | `intent_handlers.py` |
| `restock_alert` | `handle_restock_alert` | `intent_handlers.py` |

### Response Shape (Executa data)

```json
{
  "success": true,
  "data": {
    "query_type": "restock_alert",
    "language": "id",
    "message": "Produk yang perlu restock (3):\n  - **Indomie** ...",
    "actions_taken": ["restock_alert_query"],
    "items": [
      {
        "name": "Indomie Goreng",
        "stock_current": 5,
        "stock_minimum": 10,
        "unit": "pcs",
        "status": "hampir habis"
      }
    ]
  }
}
```

### Test Cases

| Input | Expected |
|-------|----------|
| `restock_alert`, lang=id | List products where stock ? minimum |
| `check_product`, name="Indomie" | Single product stock status |
| `check_product`, name="xyz" | Product not found message |
| `check_product`, ambiguous name | Disambiguation list |

---

## 8.3 Tool: get_sales

### Parameters

| Name | Type | Required | Values |
|------|------|----------|--------|
| `period` | string | no | `today` (default), `week` |
| `language` | string | no | `id`, `en` |

### Handler Mapping

| period | Wargio Handler | Internal rentang |
|--------|----------------|------------------|
| `today` | `handle_sales_report` | `hari_ini` |
| `week` | `handle_sales_report` | `minggu_ini` |

Implementation note: pass synthetic `pesan` or call handler internals directly with period param adapter.

### Test Cases

| Input | Expected |
|-------|----------|
| `period=today` | Today's revenue + transaction count |
| `period=week` | Last 7 days revenue |
| No sales in period | "Belum ada penjualan..." message |

---

## 8.4 Tool: get_debts

### Parameters

| Name | Type | Required | Values |
|------|------|----------|--------|
| `query_type` | string | yes | `check_customer`, `list_all` |
| `customer_name` | string | no | Required for `check_customer` |
| `language` | string | no | `id`, `en` |

### Handler Mapping

| query_type | Wargio Handler |
|------------|----------------|
| `check_customer` | `handle_check_debt` |
| `list_all` | `handle_debt_collection` |

### Test Cases

| Input | Expected |
|-------|----------|
| `check_customer`, name="Budi" | Debt total + breakdown |
| `check_customer`, not found | Not found message |
| `list_all` | All customers with outstanding debt |

---

## 8.5 Tool: record_payment

### Two-Phase Design

Wargio original requires confirmation before DB write. Anna Edition preserves this via explicit `action` parameter.

### Parameters

| Name | Type | Required | When |
|------|------|----------|------|
| `action` | string | yes | `prepare` or `confirm` |
| `customer_name` | string | prepare | Customer name |
| `amount` | number | prepare | Payment amount IDR |
| `draft_id` | string | confirm | From prepare response |
| `language` | string | no | `id`, `en` |

### Flow

```text
1. Agent calls record_payment(action="prepare", customer_name="Budi", amount=50000)
   ? Executa: siapkan_record_payment
   ? Store draft in APS: key="draft/{draft_id}"
   ? Return: { draft_id, summary, requires_confirmation: true }

2. Agent shows summary, asks user to confirm

3a. User confirms:
   Agent calls record_payment(action="confirm", draft_id="...")
   ? Load draft from APS
   ? eksekusi_record_payment
   ? Delete draft from APS
   ? Return: { success, message, actions_taken }

3b. User cancels:
   Agent does NOT call confirm (or future action="cancel")
   ? Draft expires via TTL (30 min, matching konfirmasi.py)
```

### APS Draft Schema

```json
{
  "tipe": "record_payment",
  "customer_id": "...",
  "customer_name": "Budi",
  "amount": 50000,
  "ringkasan": "...",
  "created_at": "ISO8601"
}
```

Key: `draft/{uuid}`, scope: `tool`, TTL: 1800 seconds.

### Test Cases

| Step | Expected |
|------|----------|
| prepare valid | Draft summary, no DB write |
| confirm valid | Debt reduced, transaction recorded |
| confirm expired draft | Error, no write |
| prepare invalid customer | Error message |
| prepare amount > debt | Warning or error per write_handlers logic |

---

## 8.6 system_prompt_addendum (MVP)

```text
You are Wargio, an AI business assistant for Indonesian warung (micro-retail) owners.

Capabilities (use tools, never invent data):
- get_inventory: check stock or list restock alerts
- get_sales: today or weekly revenue
- get_debts: check one customer or list all debtors
- record_payment: ALWAYS prepare first, show summary, wait for explicit confirmation ("ya"/"yes"), then confirm

Rules:
- Respond in the same language the user writes (Bahasa Indonesia or English)
- All monetary values in Indonesian Rupiah (Rp)
- For ambiguous product/customer names, ask user to clarify
- Never skip payment confirmation
```

---

## 8.7 Anna App UI (MVP)

Minimal dashboard — 3 cards + 3 quick actions:

| UI Element | Tool Call |
|------------|-----------|
| Card: Stok Kritis | `get_inventory(restock_alert)` |
| Card: Hutang Terbesar | `get_debts` or custom aggregate |
| Card: Omzet Hari Ini | `get_sales(today)` |
| Quick: "Cek Stok" | opens Agent or invokes inventory |
| Quick: "Laporan Minggu" | `get_sales(week)` |
| Quick: "Daftar Hutang" | `get_debts(list_all)` |

Primary UX remains `#wargio` in Anna chat.

---

## 8.8 Acceptance Criteria (MVP Complete)

- [ ] All 4 tools pass standalone Executa smoke test
- [ ] All 4 tools work via `#wargio` in `anna-app dev`
- [ ] UI dashboard cards render data from tools
- [ ] `record_payment` requires confirmation — no accidental writes
- [ ] Demo DB only — no production credentials
- [ ] Bilingual responses (ID/EN) work
- [ ] `anna-app validate --strict` passes

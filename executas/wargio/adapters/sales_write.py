"""Adapter: record_sale tool → wargio_core write handlers.

Two-phase flow (same pattern as record_payment):
  1. prepare: validate items, check stock, store draft, return summary
  2. confirm: load draft by draft_id, execute atomic sale write
  3. cancel: delete draft without writing

Items format: [{"product_name": "indomie", "qty": 3}, ...]
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from wargio_core.db.koneksi import dapatkan_database
from wargio_core.services.atlas_tools import mcp_find, mcp_update_one, mcp_insert_one
from wargio_core.services.produk import resolve_produk_tunggal
from wargio_core.util.format import format_rupiah
from wargio_core.util.lokalisasi import konteks_bahasa, label_metode_bayar, t

# In-memory draft store
_drafts: dict[str, dict[str, Any]] = {}
_DRAFT_TTL = timedelta(minutes=30)


def _cleanup_expired() -> None:
    now = datetime.now(timezone.utc)
    expired = [
        k for k, v in _drafts.items()
        if now - datetime.fromisoformat(v["created_at"]) > _DRAFT_TTL
    ]
    for k in expired:
        del _drafts[k]


async def _prepare(args: dict) -> dict:
    """Validate sale items, check stock, store draft."""
    items_raw: list[dict] = args.get("items", [])
    payment_method: str = args.get("payment_method", "tunai")
    customer_name: str | None = args.get("customer_name")
    language: str = args.get("language", "id")

    if not items_raw:
        return {
            "success": False,
            "error": t(
                'Item penjualan wajib diisi. Format: [{"product_name": "indomie", "qty": 3}]',
                'Sale items required. Format: [{"product_name": "indomie", "qty": 3}]',
            ),
        }

    with konteks_bahasa(language):
        db = await dapatkan_database()

        items_resolved: list[dict[str, Any]] = []
        aksi_all: list[str] = []

        for item in items_raw:
            nama = item.get("product_name", "").strip()
            qty = int(item.get("qty", 0))

            if not nama:
                return {"success": False, "error": t("Nama produk kosong.", "Product name empty.")}
            if qty <= 0:
                return {
                    "success": False,
                    "error": t(
                        f'Jumlah tidak valid untuk "{nama}". Harus lebih dari 0.',
                        f'Invalid quantity for "{nama}". Must be greater than 0.',
                    ),
                }

            produk, opsi, aksi_cari = await resolve_produk_tunggal(db, nama)
            aksi_all.extend(aksi_cari)

            if opsi:
                baris = "\n".join(f"  {i + 1}. {p['name']}" for i, p in enumerate(opsi))
                return {
                    "success": False,
                    "error": t(
                        f'Produk "{nama}" ambigu. Maksudnya yang mana?\n{baris}',
                        f'Product "{nama}" is ambiguous. Which one?\n{baris}',
                    ),
                }
            if not produk:
                return {
                    "success": False,
                    "error": t(
                        f'Produk "{nama}" tidak ditemukan.',
                        f'Product "{nama}" not found.',
                    ),
                }
            if produk["stock_current"] < qty:
                return {
                    "success": False,
                    "error": t(
                        f"Stok **{produk['name']}** tidak cukup. "
                        f"Tersedia {produk['stock_current']} {produk['unit']}, diminta {qty}.",
                        f"**{produk['name']}** stock insufficient. "
                        f"Available {produk['stock_current']} {produk['unit']}, requested {qty}.",
                    ),
                }

            harga = produk["price_sell"]
            items_resolved.append({
                "product_id": str(produk["_id"]),
                "product_name": produk["name"],
                "sku": produk.get("sku", ""),
                "qty": qty,
                "price": harga,
                "subtotal": harga * qty,
                "unit": produk["unit"],
            })

        total = sum(i["subtotal"] for i in items_resolved)

        # Resolve customer for credit sales
        customer_id: str | None = None
        resolved_customer_name: str | None = None

        if payment_method == "hutang":
            if not customer_name:
                return {
                    "success": False,
                    "error": t(
                        'Penjualan hutang perlu nama customer.',
                        'Credit sales need a customer name.',
                    ),
                }
            hasil, _ = await mcp_find(
                db, "customers",
                {"name": {"$regex": customer_name, "$options": "i"}},
                limit=3,
            )
            if len(hasil) == 0:
                return {
                    "success": False,
                    "error": t(
                        f'Customer "{customer_name}" tidak ditemukan.',
                        f'Customer "{customer_name}" not found.',
                    ),
                }
            if len(hasil) > 1:
                baris = "\n".join(f"  {i + 1}. {c['name']}" for i, c in enumerate(hasil))
                return {
                    "success": False,
                    "error": t(
                        f"Ada beberapa pelanggan yang cocok:\n{baris}",
                        f"Several customers match:\n{baris}",
                    ),
                }
            customer_id = str(hasil[0]["_id"])
            resolved_customer_name = hasil[0]["name"]

        # Create draft
        draft_id = str(uuid.uuid4())
        draft = {
            "tipe": "record_sale",
            "draft_id": draft_id,
            "items": items_resolved,
            "total": total,
            "payment_method": payment_method,
            "customer_id": customer_id,
            "customer_name": resolved_customer_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        _cleanup_expired()
        _drafts[draft_id] = draft

        # Build summary
        baris_items = "\n".join(
            f"  - {i['qty']}x **{i['product_name']}** "
            f"@ {format_rupiah(i['price'])} = {format_rupiah(i['subtotal'])}"
            for i in items_resolved
        )
        metode = label_metode_bayar(payment_method)
        cust_line = ""
        if payment_method == "hutang" and resolved_customer_name:
            cust_line = t(
                f"\nCustomer: **{resolved_customer_name}** (bon/hutang)\n",
                f"\nCustomer: **{resolved_customer_name}** (on credit)\n",
            )

        summary = (
            t("Konfirmasi penjualan ini?\n", "Confirm this sale?\n")
            + baris_items
            + f"\n\n**Total: {format_rupiah(total)}** ({metode})"
            + cust_line
            + t(
                "\n\nBalas **ya** untuk mencatat, atau **batal** untuk membatalkan.",
                "\n\nReply **yes** to record, or **cancel** to abort.",
            )
        )

        return {
            "success": True,
            "data": {
                "draft_id": draft_id,
                "summary": summary,
                "requires_confirmation": True,
                "items": items_resolved,
                "total": total,
                "payment_method": payment_method,
                "customer_name": resolved_customer_name,
            },
        }


async def _confirm(args: dict) -> dict:
    """Execute the sale: decrement stock, insert transaction, update debt if credit."""
    draft_id: str = args.get("draft_id", "").strip()
    language: str = args.get("language", "id")

    if not draft_id:
        return {"success": False, "error": "draft_id is required for confirm action."}

    _cleanup_expired()
    draft = _drafts.get(draft_id)

    if not draft:
        with konteks_bahasa(language):
            return {
                "success": False,
                "error": t(
                    "Draft penjualan tidak ditemukan atau sudah kedaluwarsa. Ulangi dari awal.",
                    "Sale draft not found or expired. Please start over.",
                ),
            }

    with konteks_bahasa(language):
        db = await dapatkan_database()
        from bson import ObjectId

        sekarang = datetime.now(timezone.utc)
        aksi_all: list[str] = []

        # Decrement stock for each item
        for item in draft["items"]:
            modified, aksi = await mcp_update_one(
                db,
                "products",
                {
                    "_id": ObjectId(item["product_id"]),
                    "stock_current": {"$gte": item["qty"]},
                },
                {
                    "$inc": {"stock_current": -item["qty"]},
                    "$set": {"updated_at": sekarang},
                },
            )
            aksi_all.extend(aksi)
            if modified == 0:
                return {
                    "success": False,
                    "error": t(
                        f"Stok **{item['product_name']}** tidak cukup lagi. Ulangi dari awal.",
                        f"**{item['product_name']}** stock insufficient. Please start over.",
                    ),
                }

        # Insert transaction
        dokumen_tx = {
            "type": "sale",
            "items": [
                {
                    "product_id": ObjectId(i["product_id"]),
                    "product_name": i["product_name"],
                    "qty": i["qty"],
                    "price": i["price"],
                    "subtotal": i["subtotal"],
                }
                for i in draft["items"]
            ],
            "total": draft["total"],
            "payment_method": draft["payment_method"],
            "customer_id": ObjectId(draft["customer_id"]) if draft.get("customer_id") else None,
            "notes": "Catat via Wargio agent",
            "created_at": sekarang,
        }
        _, aksi_ins = await mcp_insert_one(db, "transactions", dokumen_tx)
        aksi_all.extend(aksi_ins)

        # Update customer debt if credit sale
        if draft["payment_method"] == "hutang" and draft.get("customer_id"):
            ringkasan_item = ", ".join(f"{i['qty']}x {i['product_name']}" for i in draft["items"])
            entri_hutang = {
                "amount": draft["total"],
                "description": f"Bon penjualan: {ringkasan_item}",
                "date": sekarang,
                "paid": False,
                "paid_date": None,
            }
            _, aksi_hutang = await mcp_update_one(
                db,
                "customers",
                {"_id": ObjectId(draft["customer_id"])},
                {
                    "$inc": {"debt_total": draft["total"]},
                    "$push": {"debt_history": entri_hutang},
                },
            )
            aksi_all.extend(aksi_hutang)

        # Remove draft
        del _drafts[draft_id]

        baris = "\n".join(f"  - {i['qty']}x {i['product_name']}" for i in draft["items"])
        teks_hutang = ""
        if draft["payment_method"] == "hutang" and draft.get("customer_name"):
            teks_hutang = t(
                f"\nHutang **{draft['customer_name']}** bertambah **{format_rupiah(draft['total'])}**.",
                f"\n**{draft['customer_name']}** debt increased by **{format_rupiah(draft['total'])}**.",
            )

        metode = label_metode_bayar(draft["payment_method"])
        return {
            "success": True,
            "data": {
                "message": t(
                    f"Penjualan **berhasil dicatat**.\n{baris}\n"
                    f"Total: **{format_rupiah(draft['total'])}** ({metode}).{teks_hutang}",
                    f"Sale **recorded successfully**.\n{baris}\n"
                    f"Total: **{format_rupiah(draft['total'])}** ({metode}).{teks_hutang}",
                ),
                "actions": aksi_all,
                "total": draft["total"],
                "items_count": len(draft["items"]),
            },
        }


async def _cancel(args: dict) -> dict:
    """Cancel a pending sale draft."""
    draft_id: str = args.get("draft_id", "").strip()
    language: str = args.get("language", "id")

    if not draft_id:
        return {"success": False, "error": "draft_id is required for cancel action."}

    _cleanup_expired()
    removed = _drafts.pop(draft_id, None)

    with konteks_bahasa(language):
        if removed:
            return {
                "success": True,
                "data": {"message": t("Penjualan dibatalkan.", "Sale cancelled."), "cancelled": True},
            }
        return {
            "success": True,
            "data": {
                "message": t(
                    "Draft tidak ditemukan (mungkin sudah kedaluwarsa).",
                    "Draft not found (may have expired).",
                ),
                "cancelled": False,
            },
        }


async def run_record_sale(args: dict) -> dict:
    """Dispatch record_sale based on action param."""
    action = args.get("action", "").strip().lower()

    if action == "prepare":
        return await _prepare(args)
    elif action == "confirm":
        return await _confirm(args)
    elif action == "cancel":
        return await _cancel(args)
    else:
        return {
            "success": False,
            "error": f"Invalid action: '{action}'. Must be 'prepare', 'confirm', or 'cancel'.",
        }

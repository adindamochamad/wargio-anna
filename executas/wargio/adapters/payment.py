"""Adapter: record_payment tool → wargio_core write handlers.

Two-phase flow:
  1. prepare: validate customer + amount, store draft, return summary
  2. confirm: load draft by draft_id, execute atomic write
  3. cancel: delete draft without writing

Drafts are stored in-memory keyed by uuid4 draft_id with 30-min TTL.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from wargio_core.db.koneksi import dapatkan_database
from wargio_core.services.atlas_tools import mcp_find, mcp_update_one, mcp_insert_one
from wargio_core.services.transaksi_atomik import jalankan_dalam_transaksi
from wargio_core.util.format import format_rupiah
from wargio_core.util.lokalisasi import konteks_bahasa, t

# In-memory draft store: draft_id → draft dict
_drafts: dict[str, dict[str, Any]] = {}
_DRAFT_TTL = timedelta(minutes=30)


def _cleanup_expired() -> None:
    """Remove expired drafts on access."""
    now = datetime.now(timezone.utc)
    expired = [
        k for k, v in _drafts.items()
        if now - datetime.fromisoformat(v["created_at"]) > _DRAFT_TTL
    ]
    for k in expired:
        del _drafts[k]


async def _prepare(args: dict) -> dict:
    """Validate payment and store draft. No DB write yet."""
    customer_name: str = args.get("customer_name", "").strip()
    amount: int | float = args.get("amount", 0)
    language: str = args.get("language", "id")

    if not customer_name:
        return {
            "success": False,
            "error": t(
                'Nama customer wajib diisi. Contoh: "Bu Sari"',
                'Customer name is required. Example: "Bu Sari"',
            ),
        }

    if not amount or amount <= 0:
        return {
            "success": False,
            "error": t(
                "Jumlah pembayaran harus lebih dari 0.",
                "Payment amount must be greater than 0.",
            ),
        }

    with konteks_bahasa(language):
        db = await dapatkan_database()

        # Find customer
        hasil, aksi = await mcp_find(
            db,
            "customers",
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
                    f"Ada beberapa pelanggan yang cocok:\n{baris}\nTolong spesifikkan nama lengkap.",
                    f"Several customers match:\n{baris}\nPlease specify the full name.",
                ),
            }

        customer = hasil[0]
        hutang = customer.get("debt_total", 0)

        if hutang <= 0:
            return {
                "success": False,
                "error": t(
                    f"{customer['name']} tidak punya hutang aktif.",
                    f"{customer['name']} has no outstanding debt.",
                ),
            }

        if amount > hutang:
            return {
                "success": False,
                "error": t(
                    f"Pembayaran {format_rupiah(amount)} melebihi hutang "
                    f"{format_rupiah(hutang)}. Tolong sesuaikan jumlahnya.",
                    f"Payment {format_rupiah(amount)} exceeds debt "
                    f"{format_rupiah(hutang)}. Please adjust the amount.",
                ),
            }

        # Create draft
        draft_id = str(uuid.uuid4())
        draft = {
            "tipe": "record_payment",
            "draft_id": draft_id,
            "customer_id": str(customer["_id"]),
            "customer_name": customer["name"],
            "amount": int(amount),
            "debt_before": hutang,
            "debt_after": hutang - int(amount),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        _cleanup_expired()
        _drafts[draft_id] = draft

        jumlah_fmt = format_rupiah(draft["amount"])
        sisa_fmt = format_rupiah(draft["debt_after"])
        summary = t(
            f"Konfirmasi pembayaran hutang **{draft['customer_name']}**?\n"
            f"  - Jumlah bayar: **{jumlah_fmt}**\n"
            f"  - Sisa hutang setelah bayar: **{sisa_fmt}**\n\n"
            "Balas **ya** untuk mencatat, atau **batal** untuk membatalkan.",
            f"Confirm debt payment for **{draft['customer_name']}**?\n"
            f"  - Payment amount: **{jumlah_fmt}**\n"
            f"  - Remaining debt: **{sisa_fmt}**\n\n"
            "Reply **yes** to record, or **cancel** to abort.",
        )

        return {
            "success": True,
            "data": {
                "draft_id": draft_id,
                "summary": summary,
                "requires_confirmation": True,
                "customer_name": draft["customer_name"],
                "amount": draft["amount"],
                "debt_before": draft["debt_before"],
                "debt_after": draft["debt_after"],
            },
        }


async def _confirm(args: dict) -> dict:
    """Load draft and execute atomic payment write."""
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
                    "Draft pembayaran tidak ditemukan atau sudah kedaluwarsa. "
                    "Silakan ulangi dari awal.",
                    "Payment draft not found or expired. Please start over.",
                ),
            }

    with konteks_bahasa(language):
        db = await dapatkan_database()

        from bson import ObjectId

        cid = ObjectId(draft["customer_id"])
        jumlah = draft["amount"]
        sekarang = datetime.now(timezone.utc)

        # Load current customer state
        cust = await db.customers.find_one({"_id": cid})
        if not cust:
            del _drafts[draft_id]
            return {
                "success": False,
                "error": t("Customer tidak ditemukan.", "Customer not found."),
            }

        # Mark debt entries as paid (FIFO)
        sisa_bayar = jumlah
        riwayat_baru = []
        for entri in cust.get("debt_history", []):
            salinan = dict(entri)
            if not salinan.get("paid") and sisa_bayar > 0:
                if salinan["amount"] <= sisa_bayar:
                    salinan["paid"] = True
                    salinan["paid_date"] = sekarang
                    sisa_bayar -= salinan["amount"]
                else:
                    salinan["amount"] -= sisa_bayar
                    sisa_bayar = 0
            riwayat_baru.append(salinan)

        # Execute writes — try atomic transaction first, fallback to direct for standalone/M0
        aksi_transaksi: list[str] = []

        async def _do_writes(session=None) -> list[str]:
            aksi_dalam: list[str] = []
            _, aksi_upd = await mcp_update_one(
                db,
                "customers",
                {"_id": cid},
                {
                    "$set": {
                        "debt_total": draft["debt_after"],
                        "debt_history": riwayat_baru,
                    }
                },
                session=session,
            )
            aksi_dalam.extend(aksi_upd)

            _, aksi_ins = await mcp_insert_one(
                db,
                "transactions",
                {
                    "type": "adjustment",
                    "items": [],
                    "total": jumlah,
                    "payment_method": "tunai",
                    "customer_id": cid,
                    "notes": f"Pembayaran hutang {draft['customer_name']}",
                    "created_at": sekarang,
                },
                session=session,
            )
            aksi_dalam.extend(aksi_ins)
            return aksi_dalam

        try:
            # Try transactional write (requires replica set)
            from pymongo.asynchronous.client_session import AsyncClientSession

            async def _jalankan(sesi: AsyncClientSession) -> list[str]:
                return await _do_writes(session=sesi)

            aksi_transaksi = await jalankan_dalam_transaksi(db, _jalankan)
            aksi_transaksi.append("transaksi_atomik")
        except Exception as tx_err:
            # Fallback: direct writes for standalone/M0 (demo environment)
            if "Transaction numbers" in str(tx_err) or "IllegalOperation" in str(tx_err):
                try:
                    aksi_transaksi = await _do_writes(session=None)
                    aksi_transaksi.append("direct_write_standalone")
                except Exception:
                    return {
                        "success": False,
                        "error": t(
                            "Gagal mencatat pembayaran — coba lagi.",
                            "Failed to record payment — please try again.",
                        ),
                    }
            else:
                return {
                    "success": False,
                    "error": t(
                        "Gagal mencatat pembayaran — perubahan dibatalkan. Coba lagi.",
                        "Failed to record payment — changes rolled back. Please try again.",
                    ),
                }

        # Remove draft after successful write
        del _drafts[draft_id]

        return {
            "success": True,
            "data": {
                "message": t(
                    f"Pembayaran hutang **{draft['customer_name']}** "
                    f"**{format_rupiah(jumlah)}** berhasil dicatat.\n"
                    f"Sisa hutang: **{format_rupiah(draft['debt_after'])}**.",
                    f"Debt payment for **{draft['customer_name']}** "
                    f"**{format_rupiah(jumlah)}** recorded successfully.\n"
                    f"Remaining debt: **{format_rupiah(draft['debt_after'])}**.",
                ),
                "actions": ["mcp:updateOne", "mcp:insertOne", "transaksi_atomik", *aksi_transaksi],
                "customer_name": draft["customer_name"],
                "amount": jumlah,
                "debt_after": draft["debt_after"],
            },
        }


async def _cancel(args: dict) -> dict:
    """Cancel a pending draft without writing."""
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
                "data": {
                    "message": t(
                        "Pembayaran dibatalkan. Draft dihapus.",
                        "Payment cancelled. Draft removed.",
                    ),
                    "cancelled": True,
                },
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


async def run_record_payment(args: dict) -> dict:
    """Dispatch record_payment based on action param."""
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

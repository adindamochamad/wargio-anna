"""Alur konfirmasi write intent — simpan di in-memory dict (Executa single-process)."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from pymongo.asynchronous.database import AsyncDatabase

from wargio_core.util.lokalisasi import label_metode_bayar, t

# Draft write kedaluwarsa setelah 30 menit tanpa konfirmasi
BATAS_KEDALUWARSA_PENDING = timedelta(minutes=30)

# Kata konfirmasi / batal
KATA_KONFIRMASI = frozenset({
    "ya", "iya", "ok", "oke", "setuju", "lanjut", "lanjutkan",
    "konfirmasi", "benar", "betul", "sip", "yoi", "gas", "jadi",
    "yap", "yep", "iyalah", "yasudah", "ya sudah",
    "yes", "confirm", "confirmed", "sure", "go ahead",
})
KATA_BATAL = frozenset({
    "tidak", "batal", "cancel", "gak jadi", "ga jadi", "jangan",
    "no", "nope", "ga", "gak", "enggak",
})

# Partikel penegas Bahasa Indonesia yang tidak mengubah makna konfirmasi
_PARTIKEL = r"(?:\s+(?:dong|deh|lah|pak|bu|nih|ya|saja|aja|dah|lho|kok))?"

# --- In-memory pending storage (keyed by session_id) ---
_pending_store: dict[str, dict[str, Any]] = {}


def normalisasi_konfirmasi(pesan: str) -> str:
    return pesan.lower().strip().rstrip(".,!?")


def adalah_konfirmasi(pesan: str) -> bool:
    teks = normalisasi_konfirmasi(pesan)
    if teks in KATA_KONFIRMASI:
        return True
    # "ya dong", "ok deh", "iya lah", "gas lah", dll.
    return bool(re.match(
        rf"^(ya|iya|ok|oke|setuju|gas|jadi|sip){_PARTIKEL}\s*[,!]?\s*$",
        teks,
    ))


def adalah_batal(pesan: str) -> bool:
    teks = normalisasi_konfirmasi(pesan)
    if teks in KATA_BATAL:
        return True
    return teks.startswith("batal") or teks.startswith("cancel")


async def simpan_pending(
    db: AsyncDatabase,
    session_id: str,
    data_pending: dict[str, Any],
) -> None:
    """Simpan aksi write yang menunggu konfirmasi user (in-memory)."""
    data_pending["dibuat_pada"] = datetime.now(timezone.utc).isoformat()
    _pending_store[session_id] = data_pending


async def hapus_pending(db: AsyncDatabase, session_id: str) -> None:
    """Hapus pending dari in-memory store."""
    _pending_store.pop(session_id, None)


def _pending_kedaluwarsa(data_pending: dict[str, Any]) -> bool:
    teks_waktu = data_pending.get("dibuat_pada")
    if not teks_waktu:
        return False
    try:
        dibuat = datetime.fromisoformat(teks_waktu)
        if dibuat.tzinfo is None:
            dibuat = dibuat.replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    return datetime.now(timezone.utc) - dibuat > BATAS_KEDALUWARSA_PENDING


async def ambil_pending(
    db: AsyncDatabase,
    session_id: str,
) -> Optional[dict[str, Any]]:
    """Ambil pending; hapus otomatis jika sudah kedaluwarsa."""
    pending = _pending_store.get(session_id)
    if not pending:
        return None
    if _pending_kedaluwarsa(pending):
        await hapus_pending(db, session_id)
        return None
    return pending


def format_ringkasan_penjualan(draft: dict[str, Any]) -> str:
    from wargio_core.util.format import format_rupiah

    baris = []
    for item in draft["items"]:
        baris.append(
            f"  - {item['qty']}x **{item['product_name']}** "
            f"@ {format_rupiah(item['price'])} = {format_rupiah(item['subtotal'])}"
        )
    total_teks = format_rupiah(draft["total"])
    metode = label_metode_bayar(draft.get("payment_method", "tunai"))
    baris_customer = ""
    if draft.get("payment_method") == "hutang" and draft.get("customer_name"):
        baris_customer = t(
            f"\nCustomer: **{draft['customer_name']}** (bon/hutang)\n",
            f"\nCustomer: **{draft['customer_name']}** (on credit)\n",
        )
    return (
        t(
            "Konfirmasi penjualan ini, Bu/Pak?\n",
            "Confirm this sale?\n",
        )
        + "\n".join(baris)
        + f"\n\n**Total: {total_teks}** ({metode})"
        + baris_customer
        + t(
            "\n\nBalas **ya** untuk mencatat, atau **batal** untuk membatalkan.",
            "\n\nReply **yes** to record, or **cancel** to abort.",
        )
    )


def format_ringkasan_pembayaran(draft: dict[str, Any]) -> str:
    from wargio_core.util.format import format_rupiah

    jumlah = format_rupiah(draft["amount"])
    sisa = format_rupiah(draft["debt_after"])
    return (
        t(
            f"Konfirmasi pembayaran hutang **{draft['customer_name']}**?\n"
            f"  - Jumlah bayar: **{jumlah}**\n"
            f"  - Sisa hutang setelah bayar: **{sisa}**\n\n"
            "Balas **ya** untuk mencatat, atau **batal** untuk membatalkan.",
            f"Confirm debt payment for **{draft['customer_name']}**?\n"
            f"  - Payment amount: **{jumlah}**\n"
            f"  - Remaining debt: **{sisa}**\n\n"
            "Reply **yes** to record, or **cancel** to abort.",
        )
    )

"""Handler write intent — record_sale dan record_payment dengan konfirmasi."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase

from wargio_core.services.atlas_tools import mcp_insert_one, mcp_update_one
from wargio_core.services.ekstrak_entitas import (
    ekstrak_item_penjualan,
    ekstrak_pembayaran_hutang,
    pisahkan_customer_dari_penjualan,
)
from wargio_core.services.disambiguasi import (
    format_pesan_pilih_ulang,
    parse_pilihan_opsi,
    ringkas_opsi_produk,
)
from wargio_core.services.konfirmasi import (
    format_ringkasan_pembayaran,
    format_ringkasan_penjualan,
    hapus_pending,
    simpan_pending,
)
from wargio_core.services.produk import resolve_produk_tunggal
from wargio_core.services.transaksi_atomik import jalankan_dalam_transaksi
from wargio_core.util.format import format_rupiah
from wargio_core.util.lokalisasi import label_metode_bayar, t


class StokKonfirmasiGagal(Exception):
    """Stok berubah setelah draft — konfirmasi tidak boleh menulis ke Atlas."""

    def __init__(self, nama_produk: str, qty_diminta: int, stok_tersedia: int | None = None) -> None:
        self.nama_produk = nama_produk
        self.qty_diminta = qty_diminta
        self.stok_tersedia = stok_tersedia


async def _resolve_customer(
    db: AsyncDatabase,
    nama: str,
) -> tuple[Optional[dict[str, Any]], list[dict[str, Any]]]:
    from wargio_core.services.atlas_tools import mcp_find

    hasil, _ = await mcp_find(
        db,
        "customers",
        {"name": {"$regex": nama, "$options": "i"}},
        limit=3,
    )
    if len(hasil) == 1:
        return hasil[0], []
    if len(hasil) > 1:
        return None, hasil
    return None, []


def _item_penjualan_ke_baris(
    produk: dict[str, Any],
    qty: int,
) -> dict[str, Any]:
    harga = produk["price_sell"]
    return {
        "product_id": str(produk["_id"]),
        "product_name": produk["name"],
        "sku": produk.get("sku", ""),
        "qty": qty,
        "price": harga,
        "subtotal": harga * qty,
        "stock_sebelum": produk["stock_current"],
    }


async def _simpan_pending_disambiguasi_penjualan(
    db: AsyncDatabase,
    session_id: str,
    *,
    pesan_asli: str,
    item_mentah: list[tuple[int, str]],
    item_siap: list[dict[str, Any]],
    indeks_ambigu: int,
    nama_ambigu: str,
    opsi: list[dict[str, Any]],
) -> None:
    await simpan_pending(
        db,
        session_id,
        {
            "tipe": "disambiguasi_penjualan",
            "pesan_asli": pesan_asli,
            "item_mentah": [[q, n] for q, n in item_mentah],
            "item_siap": item_siap,
            "indeks_ambigu": indeks_ambigu,
            "nama_ambigu": nama_ambigu,
            "opsi": [ringkas_opsi_produk(p) for p in opsi],
        },
    )


async def _lanjutkan_siapkan_record_sale(
    db: AsyncDatabase,
    session_id: str,
    pesan_asli: str,
    item_mentah: list[tuple[int, str]],
    item_siap: list[dict[str, Any]],
    mulai_indeks: int,
) -> tuple[str, list[str]]:
    """Resolve item penjualan dari indeks tertentu; simpan pending jika ambigu."""
    aksi = ["mcp:find"]

    for indeks in range(mulai_indeks, len(item_mentah)):
        qty, nama_produk = item_mentah[indeks]
        if qty <= 0:
            return (
                t(
                    f'Jumlah tidak valid untuk "{nama_produk}". Harus lebih dari 0.',
                    f'Invalid quantity for "{nama_produk}". Must be greater than 0.',
                ),
                ["validasi_qty_gagal"],
            )

        produk, opsi, aksi_cari = await resolve_produk_tunggal(db, nama_produk)
        aksi.extend(aksi_cari)

        if opsi:
            baris = "\n".join(
                f"  {i + 1}. {p['name']}" for i, p in enumerate(opsi)
            )
            await _simpan_pending_disambiguasi_penjualan(
                db,
                session_id,
                pesan_asli=pesan_asli,
                item_mentah=item_mentah,
                item_siap=item_siap,
                indeks_ambigu=indeks,
                nama_ambigu=nama_produk,
                opsi=opsi,
            )
            return (
                t(
                    f'Produk "{nama_produk}" ambigu. Maksudnya yang mana?\n{baris}',
                    f'Product "{nama_produk}" is ambiguous. Which one?\n{baris}',
                ),
                [*aksi, "disambiguasi_produk"],
            )
        if not produk:
            return (
                t(
                    f'Produk "{nama_produk}" tidak ditemukan.',
                    f'Product "{nama_produk}" not found.',
                ),
                [*aksi, "produk_tidak_ditemukan"],
            )
        if produk["stock_current"] < qty:
            return (
                t(
                    f"Stok **{produk['name']}** tidak cukup. "
                    f"Tersedia {produk['stock_current']} {produk['unit']}, diminta {qty}.",
                    f"**{produk['name']}** stock insufficient. "
                    f"Available {produk['stock_current']} {produk['unit']}, requested {qty}.",
                ),
                [*aksi, "stok_tidak_cukup"],
            )

        item_siap.append(_item_penjualan_ke_baris(produk, qty))

    total = sum(i["subtotal"] for i in item_siap)
    _, nama_customer_hutang = pisahkan_customer_dari_penjualan(pesan_asli)
    teks = pesan_asli.lower()
    metode = (
        "hutang"
        if any(k in teks for k in ("hutang", "bon", "credit", "on credit"))
        else "tunai"
    )

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    if metode == "hutang":
        if not nama_customer_hutang:
            return (
                t(
                    'Penjualan bon/hutang perlu nama customer. '
                    'Contoh: "jual 2 indomie bon Bu Sari"',
                    'Credit sales need a customer name. '
                    'Example: "sell 2 indomie on credit for Bu Sari"',
                ),
                ["minta_nama_customer_hutang"],
            )
        customer, opsi_cust = await _resolve_customer(db, nama_customer_hutang)
        aksi.extend(["mcp:find"])
        if opsi_cust:
            baris = "\n".join(
                f"  {i + 1}. {c['name']}" for i, c in enumerate(opsi_cust)
            )
            return (
                t(
                    f'Customer "{nama_customer_hutang}" ambigu:\n{baris}',
                    f'Customer "{nama_customer_hutang}" is ambiguous:\n{baris}',
                ),
                [*aksi, "disambiguasi_customer"],
            )
        if not customer:
            return (
                t(
                    f'Customer "{nama_customer_hutang}" tidak ditemukan.',
                    f'Customer "{nama_customer_hutang}" not found.',
                ),
                [*aksi, "customer_tidak_ditemukan"],
            )
        customer_id = str(customer["_id"])
        customer_name = customer["name"]

    draft = {
        "tipe": "record_sale",
        "items": item_siap,
        "total": total,
        "payment_method": metode,
        "customer_id": customer_id,
        "customer_name": customer_name,
    }
    await simpan_pending(db, session_id, draft)

    return format_ringkasan_penjualan(draft), [*aksi, "minta_konfirmasi"]


async def siapkan_record_sale(
    db: AsyncDatabase,
    session_id: str,
    pesan: str,
) -> tuple[str, list[str]]:
    """Validasi penjualan, simpan draft, minta konfirmasi."""
    item_mentah = ekstrak_item_penjualan(pesan)
    if not item_mentah:
        return (
            t(
                'Format penjualan kurang jelas. Contoh: '
                '"tadi jual 3 aqua sama 2 rokok" atau '
                '"jual 2 indomie bon Bu Sari"',
                'Sale format unclear. Example: '
                '"sold 3 aqua and 2 cigarettes" or '
                '"sell 2 indomie on credit for Bu Sari"',
            ),
            ["minta_detail_penjualan"],
        )

    return await _lanjutkan_siapkan_record_sale(
        db,
        session_id,
        pesan_asli=pesan,
        item_mentah=item_mentah,
        item_siap=[],
        mulai_indeks=0,
    )


async def proses_disambiguasi_penjualan(
    db: AsyncDatabase,
    session_id: str,
    pending: dict[str, Any],
    pesan: str,
) -> tuple[str, list[str], Optional[str]]:
    """
    Lanjutkan record_sale setelah user memilih opsi produk.
    Return (balasan, aksi, intent) — intent None jika masih menunggu.
    """
    opsi_ringkas = pending.get("opsi") or []
    indeks_pilihan = parse_pilihan_opsi(pesan, opsi_ringkas)
    if indeks_pilihan is None:
        return format_pesan_pilih_ulang(), ["disambiguasi_gagal"], "disambiguasi_penjualan"

    item_mentah_mentah = pending.get("item_mentah") or []
    item_mentah = [(int(q), str(n)) for q, n in item_mentah_mentah]
    item_siap = list(pending.get("item_siap") or [])
    indeks_ambigu = int(pending.get("indeks_ambigu", 0))
    qty, _ = item_mentah[indeks_ambigu]

    produk_id = opsi_ringkas[indeks_pilihan]["id"]
    produk = await db.products.find_one({"_id": ObjectId(produk_id)})
    if not produk:
        await hapus_pending(db, session_id)
        return (
            t(
                "Produk pilihan tidak ditemukan. Coba catat penjualan dari awal.",
                "Selected product not found. Please record the sale again.",
            ),
            ["produk_tidak_ditemukan"],
            None,
        )

    if produk["stock_current"] < qty:
        await hapus_pending(db, session_id)
        return (
            t(
                f"Stok **{produk['name']}** tidak cukup. "
                f"Tersedia {produk['stock_current']} {produk['unit']}, diminta {qty}.",
                f"**{produk['name']}** stock insufficient. "
                f"Available {produk['stock_current']} {produk['unit']}, requested {qty}.",
            ),
            ["stok_tidak_cukup"],
            None,
        )

    item_siap.append(_item_penjualan_ke_baris(produk, qty))
    balasan, aksi = await _lanjutkan_siapkan_record_sale(
        db,
        session_id,
        pesan_asli=str(pending.get("pesan_asli", "")),
        item_mentah=item_mentah,
        item_siap=item_siap,
        mulai_indeks=indeks_ambigu + 1,
    )

    intent = "record_sale" if "minta_konfirmasi" in aksi else "disambiguasi_penjualan"
    return balasan, aksi, intent


async def eksekusi_record_sale(
    db: AsyncDatabase,
    session_id: str,
    draft: dict[str, Any],
) -> tuple[str, list[str]]:
    """Eksekusi penjualan setelah user konfirmasi (transaksi atomik)."""
    sekarang = datetime.now(timezone.utc)
    aksi_utama = ["mcp:insertOne", "mcp:updateOne"]

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

    async def _jalankan(sesi: AsyncClientSession) -> list[str]:
        aksi_dalam: list[str] = []

        # Kurangi stok dulu dengan filter atomik — cegah race & stok negatif
        for item in draft["items"]:
            jumlah_diubah, aksi_upd = await mcp_update_one(
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
                session=sesi,
            )
            aksi_dalam.extend(aksi_upd)
            if jumlah_diubah == 0:
                from wargio_core.services.atlas_tools import mcp_find

                dokumen_stok, _ = await mcp_find(
                    db,
                    "products",
                    {"_id": ObjectId(item["product_id"])},
                    limit=1,
                )
                stok_sekarang = (
                    dokumen_stok[0].get("stock_current") if dokumen_stok else None
                )
                raise StokKonfirmasiGagal(
                    item["product_name"],
                    item["qty"],
                    stok_sekarang,
                )

        _, aksi_ins = await mcp_insert_one(
            db, "transactions", dokumen_tx, session=sesi
        )
        aksi_dalam.extend(aksi_ins)

        if draft["payment_method"] == "hutang" and draft.get("customer_id"):
            ringkasan_item = ", ".join(
                f"{i['qty']}x {i['product_name']}" for i in draft["items"]
            )
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
                session=sesi,
            )
            aksi_dalam.extend(aksi_hutang)

        return aksi_dalam

    try:
        aksi_transaksi = await jalankan_dalam_transaksi(db, _jalankan)
    except StokKonfirmasiGagal as gagal:
        await hapus_pending(db, session_id)
        if gagal.stok_tersedia is not None:
            pesan = t(
                f"Stok **{gagal.nama_produk}** tidak cukup lagi saat konfirmasi. "
                f"Tersedia {gagal.stok_tersedia} pcs, diminta {gagal.qty_diminta}. "
                "Silakan catat penjualan ulang.",
                f"**{gagal.nama_produk}** stock changed before confirmation. "
                f"Available {gagal.stok_tersedia} pcs, requested {gagal.qty_diminta}. "
                "Please record the sale again.",
            )
        else:
            pesan = t(
                f"Stok **{gagal.nama_produk}** tidak cukup lagi saat konfirmasi. "
                "Silakan catat penjualan ulang.",
                f"**{gagal.nama_produk}** stock insufficient at confirmation. "
                "Please record the sale again.",
            )
        return pesan, ["stok_konfirmasi_gagal"]
    except Exception:
        return (
            t(
                "Gagal mencatat penjualan — perubahan dibatalkan. Coba lagi sebentar.",
                "Failed to record sale — changes rolled back. Please try again.",
            ),
            ["error_transaksi_atomik"],
        )

    await hapus_pending(db, session_id)

    baris = "\n".join(
        f"  - {i['qty']}x {i['product_name']}" for i in draft["items"]
    )
    teks_hutang = ""
    if draft["payment_method"] == "hutang" and draft.get("customer_name"):
        teks_hutang = t(
            f"\nHutang **{draft['customer_name']}** bertambah **{format_rupiah(draft['total'])}**.",
            f"\n**{draft['customer_name']}** debt increased by **{format_rupiah(draft['total'])}**.",
        )

    metode_label = label_metode_bayar(draft["payment_method"])
    return (
        t(
            f"Penjualan **berhasil dicatat**.\n{baris}\n"
            f"Total: **{format_rupiah(draft['total'])}** ({metode_label})."
            f"{teks_hutang}",
            f"Sale **recorded successfully**.\n{baris}\n"
            f"Total: **{format_rupiah(draft['total'])}** ({metode_label})."
            f"{teks_hutang}",
        ),
        [*aksi_utama, *aksi_transaksi, "transaksi_atomik"],
    )


async def siapkan_record_payment(
    db: AsyncDatabase,
    session_id: str,
    pesan: str,
) -> tuple[str, list[str]]:
    """Validasi pembayaran hutang, simpan draft."""
    nama, jumlah = ekstrak_pembayaran_hutang(pesan)
    if not nama:
        return (
            t(
                'Hutang siapa yang dibayar? Contoh: "Bu Sari bayar hutang 50 ribu"',
                'Whose debt is being paid? Example: "Bu Sari pays debt 50000"',
            ),
            ["minta_nama_customer"],
        )
    if not jumlah or jumlah <= 0:
        return (
            t(
                'Jumlah pembayaran tidak valid. Contoh: "bayar hutang 50 ribu"',
                'Invalid payment amount. Example: "pay debt 50000"',
            ),
            ["validasi_jumlah_gagal"],
        )

    customer, opsi = await _resolve_customer(db, nama)
    aksi = ["mcp:find"]

    if opsi:
        baris = "\n".join(f"  {i + 1}. {c['name']}" for i, c in enumerate(opsi))
        return (
            t(
                f"Ada beberapa pelanggan yang cocok:\n{baris}",
                f"Several customers match:\n{baris}",
            ),
            [*aksi, "disambiguasi_customer"],
        )
    if not customer:
        return (
            t(f'Customer "{nama}" tidak ditemukan.', f'Customer "{nama}" not found.'),
            [*aksi, "customer_tidak_ditemukan"],
        )

    hutang = customer.get("debt_total", 0)
    if hutang <= 0:
        return (
            t(
                f"{customer['name']} tidak punya hutang aktif.",
                f"{customer['name']} has no outstanding debt.",
            ),
            aksi,
        )

    if jumlah > hutang:
        return (
            t(
                f"Pembayaran **{format_rupiah(jumlah)}** melebihi hutang "
                f"**{format_rupiah(hutang)}**. Tolong sesuaikan jumlahnya.",
                f"Payment **{format_rupiah(jumlah)}** exceeds debt "
                f"**{format_rupiah(hutang)}**. Please adjust the amount.",
            ),
            [*aksi, "jumlah_melebihi_hutang"],
        )

    draft = {
        "tipe": "record_payment",
        "customer_id": str(customer["_id"]),
        "customer_name": customer["name"],
        "amount": jumlah,
        "debt_before": hutang,
        "debt_after": hutang - jumlah,
    }
    await simpan_pending(db, session_id, draft)
    return format_ringkasan_pembayaran(draft), [*aksi, "minta_konfirmasi"]


async def eksekusi_record_payment(
    db: AsyncDatabase,
    session_id: str,
    draft: dict[str, Any],
) -> tuple[str, list[str]]:
    """Eksekusi pembayaran hutang setelah konfirmasi (transaksi atomik)."""
    sekarang = datetime.now(timezone.utc)
    aksi_utama = ["mcp:updateOne", "mcp:insertOne"]
    cid = ObjectId(draft["customer_id"])
    jumlah = draft["amount"]

    cust = await db.customers.find_one({"_id": cid})
    if not cust:
        await hapus_pending(db, session_id)
        return t("Customer tidak ditemukan.", "Customer not found."), ["error"]

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

    async def _jalankan(sesi: AsyncClientSession) -> list[str]:
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
            session=sesi,
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
            session=sesi,
        )
        aksi_dalam.extend(aksi_ins)
        return aksi_dalam

    try:
        aksi_transaksi = await jalankan_dalam_transaksi(db, _jalankan)
    except Exception:
        return (
            t(
                "Gagal mencatat pembayaran — perubahan dibatalkan. Coba lagi sebentar.",
                "Failed to record payment — changes rolled back. Please try again.",
            ),
            ["error_transaksi_atomik"],
        )

    await hapus_pending(db, session_id)
    return (
        t(
            f"Pembayaran hutang **{draft['customer_name']}** "
            f"**{format_rupiah(jumlah)}** berhasil dicatat.\n"
            f"Sisa hutang: **{format_rupiah(draft['debt_after'])}**.",
            f"Debt payment for **{draft['customer_name']}** "
            f"**{format_rupiah(jumlah)}** recorded successfully.\n"
            f"Remaining debt: **{format_rupiah(draft['debt_after'])}**.",
        ),
        [*aksi_utama, *aksi_transaksi, "transaksi_atomik"],
    )

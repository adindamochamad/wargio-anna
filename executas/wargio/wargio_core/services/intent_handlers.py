"""Handler intent Tier 1 read — query via MCP-equivalent tools."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from pymongo.asynchronous.database import AsyncDatabase

from wargio_core.services.atlas_tools import mcp_aggregate, mcp_find
from wargio_core.services.klasifikasi import ekstrak_nama_customer, ekstrak_nama_produk
from wargio_core.services.produk import resolve_produk_tunggal
from wargio_core.util.format import format_rupiah, tanggal_indonesia
from wargio_core.util.lokalisasi import ambil_bahasa, t

_NAMA_HARI_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
_NAMA_HARI_EN = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


async def handle_check_stock(
    db: AsyncDatabase,
    pesan: str,
) -> tuple[str, list[str]]:
    """Cek stok produk — MCP find products."""
    kata_kunci = ekstrak_nama_produk(pesan)
    if not kata_kunci:
        return (
            t(
                'Produk mana yang ingin dicek stoknya, Bu/Pak? '
                'Contoh: "stok mie instan berapa?"',
                'Which product stock should I check? '
                'Example: "how much instant noodle stock is left?"',
            ),
            ["minta_spesifikasi_produk"],
        )

    produk, opsi, aksi_cari = await resolve_produk_tunggal(db, kata_kunci)
    if opsi:
        label_stok = t("stok", "stock")
        baris = "\n".join(
            f"  {i + 1}. {p['name']} ({label_stok}: {p['stock_current']})"
            for i, p in enumerate(opsi)
        )
        return (
            t(
                f"Maksudnya yang mana?\n{baris}",
                f"Which one did you mean?\n{baris}",
            ),
            [*aksi_cari, "disambiguasi_produk"],
        )
    if not produk:
        return (
            t(
                f'Produk "{kata_kunci}" tidak ditemukan. '
                "Coba sebut nama yang lebih spesifik.",
                f'Product "{kata_kunci}" not found. '
                "Try a more specific name.",
            ),
            [*aksi_cari, "produk_tidak_ditemukan"],
        )

    stok = produk["stock_current"]
    minimum = produk["stock_minimum"]
    if stok <= minimum:
        status = t("hampir habis — perlu restock", "low — restock needed")
    elif stok <= minimum * 1.2:
        status = t("mendekati minimum", "near minimum")
    else:
        status = t("aman", "OK")

    balasan = t(
        f"Stok **{produk['name']}**: {stok} {produk['unit']} "
        f"(minimum {minimum}). Status: {status}.",
        f"Stock **{produk['name']}**: {stok} {produk['unit']} "
        f"(minimum {minimum}). Status: {status}.",
    )
    return balasan, [*aksi_cari, "compare_minimum"]


async def handle_check_debt(
    db: AsyncDatabase,
    pesan: str,
) -> tuple[str, list[str]]:
    """Cek hutang customer — MCP find customers."""
    nama = ekstrak_nama_customer(pesan)
    if not nama:
        return (
            t(
                'Hutang siapa yang ingin dicek? Contoh: "hutang Bu Sari berapa?"',
                'Whose debt should I check? Example: "how much debt does Bu Sari have?"',
            ),
            ["minta_nama_customer"],
        )

    hasil, aksi = await mcp_find(
        db,
        "customers",
        {"name": {"$regex": nama, "$options": "i"}},
        limit=3,
    )

    if len(hasil) == 0:
        return (
            t(
                f'Customer "{nama}" tidak ditemukan.',
                f'Customer "{nama}" not found.',
            ),
            [*aksi, "customer_tidak_ditemukan"],
        )
    if len(hasil) > 1:
        baris = "\n".join(f"  {i + 1}. {c['name']}" for i, c in enumerate(hasil))
        return (
            t(
                f"Ada beberapa yang cocok:\n{baris}",
                f"Several matches found:\n{baris}",
            ),
            [*aksi, "disambiguasi_customer"],
        )

    cust = hasil[0]
    total = cust.get("debt_total", 0)
    if total <= 0:
        return (
            t(
                f"{cust['name']} tidak punya hutang aktif.",
                f"{cust['name']} has no outstanding debt.",
            ),
            aksi,
        )

    belum_bayar = [h for h in cust.get("debt_history", []) if not h.get("paid")]
    rincian = "\n".join(
        f"  - {format_rupiah(h['amount'])} ({h.get('description', '-')})"
        for h in belum_bayar[:5]
    )
    kosong = t("  (tidak ada detail)", "  (no details)")
    return (
        t(
            f"Hutang **{cust['name']}** total **{format_rupiah(total)}**.\n"
            f"Rincian:\n{rincian or kosong}",
            f"**{cust['name']}** owes **{format_rupiah(total)}** in total.\n"
            f"Breakdown:\n{rincian or kosong}",
        ),
        [*aksi, "hitung_total_hutang"],
    )


async def handle_restock_alert(db: AsyncDatabase) -> tuple[str, list[str]]:
    """Produk stok rendah — MCP find + sort urgency."""
    filter_rendah = {"$expr": {"$lte": ["$stock_current", "$stock_minimum"]}}
    hasil, aksi = await mcp_find(
        db,
        "products",
        filter_rendah,
        limit=10,
        sort=[("stock_current", 1)],
    )

    if not hasil:
        return (
            t(
                "Semua produk masih aman, tidak ada yang perlu restock urgent.",
                "All products are fine — nothing needs urgent restock.",
            ),
            aksi,
        )

    baris = []
    for p in hasil:
        selisih = p["stock_minimum"] - p["stock_current"]
        label_kurang = t("kurang", "short by")
        baris.append(
            f"  - **{p['name']}**: {p['stock_current']}/{p['stock_minimum']} "
            f"{p['unit']} ({label_kurang} {max(selisih, 0)})"
        )
    return (
        t(
            f"Produk yang perlu restock ({len(hasil)}):\n" + "\n".join(baris),
            f"Products needing restock ({len(hasil)}):\n" + "\n".join(baris),
        ),
        [*aksi, "rank_urgency"],
    )


async def handle_sales_report(
    db: AsyncDatabase,
    pesan: str,
) -> tuple[str, list[str]]:
    """Laporan penjualan — MCP aggregate transactions."""
    zona = ZoneInfo("Asia/Jakarta")
    sekarang = datetime.now(zona)
    awal_hari = sekarang.replace(hour=0, minute=0, second=0, microsecond=0)

    teks = pesan.lower()
    if "minggu" in teks or "week" in teks:
        awal = awal_hari - timedelta(days=7)
        label = t("7 hari terakhir", "last 7 days")
    else:
        awal = awal_hari
        tanggal = tanggal_indonesia(sekarang.astimezone(timezone.utc))
        label = t(f"hari ini ({tanggal})", f"today ({tanggal})")

    awal_utc = awal.astimezone(timezone.utc)
    sekarang_utc = sekarang.astimezone(timezone.utc)

    pipeline: list[dict[str, Any]] = [
        {
            "$match": {
                "type": "sale",
                "created_at": {"$gte": awal_utc, "$lte": sekarang_utc},
            }
        },
        {
            "$group": {
                "_id": None,
                "total_omzet": {"$sum": "$total"},
                "jumlah_transaksi": {"$sum": 1},
            }
        },
    ]
    agg, aksi = await mcp_aggregate(db, "transactions", pipeline)

    if not agg:
        return (
            t(
                f"Belum ada penjualan untuk {label}.",
                f"No sales recorded for {label}.",
            ),
            aksi,
        )

    data = agg[0]
    tx_label = t("transaksi", "transactions")
    return (
        t(
            f"Pendapatan **{label}**: **{format_rupiah(data['total_omzet'])}** "
            f"dari {data['jumlah_transaksi']} transaksi.",
            f"Revenue **{label}**: **{format_rupiah(data['total_omzet'])}** "
            f"from {data['jumlah_transaksi']} {tx_label}.",
        ),
        [*aksi, "format_laporan"],
    )


async def handle_debt_collection(db: AsyncDatabase) -> tuple[str, list[str]]:
    """Daftar customer dengan hutang aktif — find + sort."""
    hasil, aksi = await mcp_find(
        db,
        "customers",
        {"debt_total": {"$gt": 0}},
        limit=15,
        sort=[("debt_total", -1)],
    )
    if not hasil:
        return (
            t(
                "Tidak ada customer dengan hutang aktif.",
                "No customers with outstanding debt.",
            ),
            aksi,
        )

    baris = []
    for c in hasil:
        baris.append(
            f"  - **{c['name']}**: {format_rupiah(c.get('debt_total', 0))}"
        )
    return (
        t(
            f"Pelanggan dengan hutang aktif ({len(hasil)}):\n" + "\n".join(baris),
            f"Customers with outstanding debt ({len(hasil)}):\n" + "\n".join(baris),
        ),
        [*aksi, "sort_debt"],
    )


async def handle_sales_forecast(db: AsyncDatabase) -> tuple[str, list[str]]:
    """Forecast sederhana — rata-rata transaksi per hari dalam seminggu (30 hari)."""
    zona = ZoneInfo("Asia/Jakarta")
    sekarang = datetime.now(zona)
    awal = (sekarang - timedelta(days=30)).astimezone(timezone.utc)
    besok = (sekarang + timedelta(days=1)).weekday()

    nama_hari = _NAMA_HARI_EN if ambil_bahasa() == "en" else _NAMA_HARI_ID

    pipeline: list[dict[str, Any]] = [
        {"$match": {"type": "sale", "created_at": {"$gte": awal}}},
        {
            "$group": {
                "_id": {"$dayOfWeek": "$created_at"},
                "jumlah_transaksi": {"$sum": 1},
                "total_omzet": {"$sum": "$total"},
            }
        },
    ]
    agg, aksi = await mcp_aggregate(db, "transactions", pipeline)

    if not agg:
        return (
            t(
                "Belum cukup data penjualan untuk perkiraan.",
                "Not enough sales data for a forecast.",
            ),
            aksi,
        )

    peta_mongo_ke_py = {2: 0, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 1: 6}
    peta_py: dict[int, dict[str, Any]] = {}
    for baris in agg:
        dow = baris["_id"]
        py_day = peta_mongo_ke_py.get(dow, 0)
        minggu = max(30 / 7, 1)
        peta_py[py_day] = {
            "avg_tx": baris["jumlah_transaksi"] / minggu,
            "avg_omzet": baris["total_omzet"] / minggu,
        }

    pred = peta_py.get(besok, {"avg_tx": 0, "avg_omzet": 0})
    if pred["avg_tx"] >= 8:
        level = t("ramai", "busy")
    elif pred["avg_tx"] >= 4:
        level = t("sedang", "moderate")
    else:
        level = t("sepi", "quiet")

    return (
        t(
            f"Perkiraan **{nama_hari[besok]}** (besok): cenderung **{level}**.\n"
            f"Rata-rata historis: ~{pred['avg_tx']:.0f} transaksi, "
            f"omzet ~{format_rupiah(pred['avg_omzet'])} per hari serupa.",
            f"Forecast for **{nama_hari[besok]}** (tomorrow): likely **{level}**.\n"
            f"Historical average: ~{pred['avg_tx']:.0f} transactions, "
            f"revenue ~{format_rupiah(pred['avg_omzet'])} on similar days.",
        ),
        [*aksi, "forecast_day_of_week"],
    )

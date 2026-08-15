#!/usr/bin/env python3
"""
Seed synthetic warung data for the Wargio Anna Edition DEMO database.

Adapted from the upstream Wargio `scripts/seed_data.py` (see
docs/09-vendor-map.md 9.4). Differences for Anna Edition:

  * Default database is `wargio_anna_demo` (NOT the upstream `wargio_demo`).
  * Refuses to write to the upstream production DB name unless
    `--allow-prod-name` is explicitly passed.
  * Synthetic data only (no real customer PII) per docs/10-security-and-data.md.
  * `--dry-run` generates and counts documents WITHOUT connecting to MongoDB,
    so the generator can be verified offline (no mongod / Atlas required).

Usage:
    python scripts/seed_data.py --dry-run          # offline generation check
    python scripts/seed_data.py                    # seed wargio_anna_demo
    MONGODB_DATABASE=... python scripts/seed_data.py
"""

from __future__ import annotations

import argparse
import asyncio
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Optional deps only needed for the live path.
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ModuleNotFoundError:  # dry-run works without python-dotenv
    pass

DEFAULT_DB = "wargio_anna_demo"
UPSTREAM_PROD_DB = "wargio_demo"

URI = os.getenv("MONGODB_URI", "").strip()
DB_NAME = os.getenv("MONGODB_DATABASE", DEFAULT_DB)
SEKARANG = datetime.now(timezone.utc)
random.seed(42)

# Katalog dasar warung — di-expand jadi 50+ SKU
KATALOG_DASAR: list[tuple] = [
    ("MIN-AQUA-600", "Air Mineral Aqua 600ml", ["aqua", "air mineral"], "minuman", 2500, 3500, "pcs"),
    ("MIN-LEMIN-600", "Teh Botol Sosro 500ml", ["teh botol", "sosro"], "minuman", 3000, 4500, "pcs"),
    ("MIN-KOPI-GOD", "Kopi Kapal Api Special", ["kopi", "kapal api"], "minuman", 1500, 2500, "pcs"),
    ("MIN-ULTRA-250", "Ultra Milk Coklat 250ml", ["ultra milk", "susu kotak"], "minuman", 4000, 5500, "pcs"),
    ("MIN-FANTA", "Fanta Orange 390ml", ["fanta"], "minuman", 3500, 5000, "pcs"),
    ("MKN-INDO-GORENG", "Indomie Goreng Original", ["indomie", "mie instan"], "makanan", 2200, 3000, "pcs"),
    ("MKN-INDO-KUAH", "Indomie Soto Mie", ["indomie kuah", "soto mie"], "makanan", 2200, 3000, "pcs"),
    ("MKN-MIE-SEDAP", "Mie Sedap Goreng", ["mie sedap"], "makanan", 2100, 2800, "pcs"),
    ("MKN-POPMIE", "Pop Mie Ayam Bawang", ["pop mie"], "makanan", 3500, 5000, "pcs"),
    ("MKN-SARI-ROT", "Roti Tawar Sari Roti", ["roti tawar"], "makanan", 12000, 15000, "pcs"),
    ("MKN-KERUPUK", "Kerupuk Udang Finna 200g", ["kerupuk"], "makanan", 8000, 10000, "bungkus"),
    ("MKN-ABON", "Abon Sapi 100g", ["abon"], "makanan", 15000, 18000, "pcs"),
    ("ROK-SAMPOERNA", "Rokok Sampoerna Mild 16", ["sampoerna", "rokok"], "rokok", 22000, 25000, "bungkus"),
    ("ROK-MARLBORO", "Rokok Marlboro Filter 20", ["marlboro"], "rokok", 28000, 32000, "bungkus"),
    ("ROK-DJI-SAM", "Rokok Dji Sam Soe 12", ["dji sam soe"], "rokok", 18000, 21000, "bungkus"),
    ("SMB-BERAS-5KG", "Beras Premium 5kg", ["beras 5kg"], "sembako", 62000, 70000, "pcs"),
    ("SMB-MINYAK-1L", "Minyak Goreng Bimoli 1L", ["minyak goreng"], "sembako", 18000, 22000, "liter"),
    ("SMB-GULA-1KG", "Gula Pasir Gulaku 1kg", ["gula"], "sembako", 14000, 17000, "kg"),
    ("SMB-TEPUNG-1KG", "Tepung Terigu Segitiga 1kg", ["tepung"], "sembako", 12000, 15000, "kg"),
    ("SMB-KOPI-ABC", "Kopi ABC Susu 10 sachet", ["kopi abc"], "sembako", 9000, 12000, "bungkus"),
]

NAMA_CUSTOMER = [
    "Bu Sari", "Pak Budi", "Bu Ani", "Pak Joko", "Bu Rina",
    "Pak Agus", "Bu Dewi", "Pak Hendra", "Bu Fitri", "Pak Rudi",
    "Bu Maya", "Pak Toni", "Bu Yuni", "Pak Eko", "Bu Lina",
    "Pak Bambang", "Bu Siti", "Pak Dedi", "Bu Wati", "Pak Udin",
]


def uri_valid() -> bool:
    if not URI or not URI.startswith("mongodb"):
        return False
    return not any(x in URI for x in ("USER", "PASSWORD", "<password>", "changeme"))


def daftar_produk() -> list[dict]:
    """Generate 52 produk dari katalog + variasi."""
    hasil: list[dict] = []
    for idx, (sku, nama, alias, kategori, beli, jual, unit) in enumerate(KATALOG_DASAR):
        stok_min = random.randint(8, 25)
        # ~40% produk stok rendah untuk tes restock
        stok = random.randint(2, stok_min - 1) if idx % 3 == 0 else random.randint(stok_min, stok_min + 40)
        hasil.append({
            "sku": sku,
            "name": nama,
            "name_aliases": alias,
            "category": kategori,
            "price_buy": beli,
            "price_sell": jual,
            "stock_current": stok,
            "stock_minimum": stok_min,
            "unit": unit,
            "supplier": "Grosir Sembako" if kategori in ("makanan", "sembako") else "Agen Minuman",
            "last_restock_date": SEKARANG - timedelta(days=random.randint(1, 14)),
            "created_at": SEKARANG,
            "updated_at": SEKARANG,
        })

    # Tambah variasi SKU hingga 52+
    varian = [
        ("MIN-AQUA-1500", "Air Mineral Aqua 1.5L", "minuman"),
        ("MIN-TEH-PUCUK", "Teh Pucuk Harum 350ml", "minuman"),
        ("MKN-INDO-REND", "Indomie Rendang", "makanan"),
        ("MKN-SARIMIE", "Mie Sedaap Ayam Bawang", "makanan"),
        ("ROK-GUDANG", "Rokok Gudang Garam Filter", "rokok"),
        ("SMB-SUSU-KTK", "Susu Kental Manis Frisian Flag", "sembako"),
        ("LNY-SABUN-LIF", "Sabun Lifebuoy Batang", "lainnya"),
        ("LNY-SAMP-RIN", "Shampoo Sunsilk Sachet", "lainnya"),
        ("LNY-PAST-GIG", "Pasta Gigi Pepsodent", "lainnya"),
        ("LNY-TISU-PRE", "Tisu Prenium 250 sheet", "lainnya"),
        ("MKN-NASI-UDK", "Nasi Uduk Bungkus", "makanan"),
        ("MIN-ES-TEH", "Es Teh Kotak 200ml", "minuman"),
        ("MKN-KACANG-G", "Kacang Garuda 200g", "makanan"),
        ("SMB-GARAM-1K", "Garam Dolpin 1kg", "sembako"),
        ("MIN-SPRITE", "Sprite 390ml", "minuman"),
        ("MKN-CHITATO", "Chitato Sapi Panggang 68g", "makanan"),
        ("ROK-LA-BOLD", "Rokok LA Bold 16", "rokok"),
        ("SMB-MIE-TEP", "Mie Telur Cap Ayam 1kg", "sembako"),
        ("LNY-DETTOL", "Dettol Sabun Cair 200ml", "lainnya"),
        ("MIN-AQUA-GEL", "Aqua Gelas 240ml", "minuman"),
        ("MKN-SUSU-UHT", "Susu UHT Full Cream 1L", "makanan"),
        ("MIN-KRIN-KLN", "Krin Krenyes 500ml", "minuman"),
        ("MKN-BISKUIT", "Biskuit Roma Kelapa", "makanan"),
        ("SMB-KECAP-IN", "Kecap Manis Indofood 520ml", "sembako"),
        ("LNY-SABUN-MU", "Sabun Molto 800ml", "lainnya"),
        ("MIN-COCA-390", "Coca Cola 390ml", "minuman"),
        ("MKN-SLAI-IND", "Selai Indomaret Strawberry", "makanan"),
        ("ROK-DUNHIL", "Rokok Dunhill Mild 16", "rokok"),
        ("SMB-SAOS-SAM", "Saos Sambal ABC 335ml", "sembako"),
        ("LNY-PLEMB-CL", "Pembersih Lantai Clorox", "lainnya"),
        ("MIN-AQUA-330", "Aqua Botol 330ml", "minuman"),
        ("MKN-WAFER-TK", "Wafer Tango Coklat", "makanan"),
    ]
    for sku, nama, kategori in varian:
        beli = random.randint(1500, 25000)
        jual = beli + random.randint(500, 5000)
        stok_min = random.randint(10, 20)
        stok = random.randint(2, stok_min - 1) if random.random() < 0.35 else random.randint(stok_min, 50)
        hasil.append({
            "sku": sku,
            "name": nama,
            "name_aliases": [nama.split()[0].lower(), nama.lower()],
            "category": kategori,
            "price_buy": beli,
            "price_sell": jual,
            "stock_current": stok,
            "stock_minimum": stok_min,
            "unit": "pcs",
            "supplier": "Grosir Sembako",
            "last_restock_date": SEKARANG - timedelta(days=random.randint(1, 20)),
            "created_at": SEKARANG,
            "updated_at": SEKARANG,
        })
    return hasil


def daftar_customer() -> list[dict]:
    customers: list[dict] = []
    for i, nama in enumerate(NAMA_CUSTOMER):
        punya_hutang = i < 14  # 14 dari 20 punya hutang
        total = random.randint(15000, 350000) if punya_hutang else 0
        riwayat = []
        if punya_hutang:
            sisa = total
            for _ in range(random.randint(1, 3)):
                jumlah = min(sisa, random.randint(10000, 80000))
                riwayat.append({
                    "amount": jumlah,
                    "description": random.choice(["Belanja sembako", "Belanja minuman", "Belanja rokok"]),
                    "date": SEKARANG - timedelta(days=random.randint(1, 21)),
                    "paid": False,
                    "paid_date": None,
                })
                sisa -= jumlah
                if sisa <= 0:
                    break
        customers.append({
            "name": nama,
            "phone": f"0812{random.randint(10000000, 99999999)}" if i % 2 == 0 else None,
            "address": f"RT {random.randint(1, 5)}" if i % 3 != 0 else None,
            "debt_total": total,
            "debt_history": riwayat,
            "created_at": SEKARANG - timedelta(days=30),
        })
    return customers


def buat_transaksi(id_produk: list, produk: list[dict], id_customer: list) -> list[dict]:
    """~210 transaksi selama 30 hari."""
    transaksi: list[dict] = []
    for hari in range(30):
        jumlah_harian = random.randint(5, 10)
        for _ in range(jumlah_harian):
            tanggal = SEKARANG - timedelta(days=hari, hours=random.randint(6, 20))
            n_item = random.randint(1, 4)
            indeks = random.sample(range(len(produk)), min(n_item, len(produk)))
            items = []
            total = 0
            for ix in indeks:
                qty = random.randint(1, 5)
                harga = produk[ix]["price_sell"]
                sub = qty * harga
                items.append({
                    "product_id": id_produk[ix],
                    "product_name": produk[ix]["name"],
                    "qty": qty,
                    "price": harga,
                    "subtotal": sub,
                })
                total += sub
            bayar_hutang = random.random() < 0.25
            transaksi.append({
                "type": "sale",
                "items": items,
                "total": total,
                "payment_method": "hutang" if bayar_hutang else random.choice(["tunai", "tunai", "transfer"]),
                "customer_id": random.choice(id_customer) if bayar_hutang else None,
                "notes": "",
                "created_at": tanggal,
            })
    return transaksi


def generate_all() -> tuple[list[dict], list[dict], list[dict]]:
    """Offline generation (no DB). Uses placeholder Object-id-like indices."""
    produk = daftar_produk()
    customers = daftar_customer()
    # Placeholder ids for dry-run (live path replaces with real ObjectIds).
    id_produk = list(range(len(produk)))
    id_customer = list(range(len(customers)))
    transaksi = buat_transaksi(id_produk, produk, customers and id_customer)
    return produk, customers, transaksi


def dry_run() -> None:
    produk, customers, transaksi = generate_all()
    n_low = sum(1 for p in produk if p["stock_current"] < p["stock_minimum"])
    n_debtors = sum(1 for c in customers if c["debt_total"] > 0)
    print("DRY-RUN (no MongoDB connection):")
    print(f"  target database : {DB_NAME}")
    print(f"  products        : {len(produk)} ({n_low} below minimum -> restock alerts)")
    print(f"  customers       : {len(customers)} ({n_debtors} with outstanding debt)")
    print(f"  transactions    : {len(transaksi)} (30 days)")
    print("  synthetic PII   : names are fictional; phones/addresses are random placeholders")
    print("OK: generation logic verified offline.")


async def seed(allow_prod_name: bool) -> None:
    if DB_NAME == UPSTREAM_PROD_DB and not allow_prod_name:
        print(
            f"REFUSED: target database is '{UPSTREAM_PROD_DB}' (upstream production name). "
            f"Anna Edition must use a separate demo DB (default '{DEFAULT_DB}'). "
            "Pass --allow-prod-name only if you really mean it."
        )
        sys.exit(2)

    if not uri_valid():
        print("GAGAL: MONGODB_URI belum valid di .env (salin .env.example -> .env).")
        sys.exit(1)

    from pymongo import AsyncMongoClient

    klien = AsyncMongoClient(URI)
    db = klien[DB_NAME]

    for nama in ("products", "transactions", "customers", "agent_sessions"):
        await db[nama].delete_many({})

    produk = daftar_produk()
    hasil_produk = await db.products.insert_many(produk)
    id_produk = list(hasil_produk.inserted_ids)

    customers = daftar_customer()
    hasil_cust = await db.customers.insert_many(customers)
    id_customer = list(hasil_cust.inserted_ids)

    transaksi = buat_transaksi(id_produk, produk, id_customer)
    await db.transactions.insert_many(transaksi)

    await klien.close()
    print(
        f"OK: Seed selesai ke '{DB_NAME}' — {len(produk)} produk, {len(customers)} customer, "
        f"{len(transaksi)} transaksi (30 hari)."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Wargio Anna Edition demo DB (synthetic data).")
    parser.add_argument("--dry-run", action="store_true", help="Generate + count offline, no DB write.")
    parser.add_argument("--allow-prod-name", action="store_true", help="Permit upstream prod DB name (unsafe).")
    args = parser.parse_args()

    if args.dry_run:
        dry_run()
        return
    asyncio.run(seed(args.allow_prod_name))


if __name__ == "__main__":
    main()

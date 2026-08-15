"""Klasifikasi intent dari pesan Bahasa Indonesia."""

from __future__ import annotations

import re
from typing import Optional

INTENT_LIST = (
    "check_stock",
    "check_debt",
    "restock_alert",
    "sales_report",
    "record_sale",
    "record_payment",
    "debt_collection",
    "sales_forecast",
    "unknown",
)

# Pola berurutan — intent spesifik / write dulu
POLA_INTENT: list[tuple[str, list[str]]] = [
    # debt_collection sebelum record_payment — hindari match "belum bayar"
    ("debt_collection", [
        r"siapa.*belum bayar", r"belum bayar hutang", r"tagih hutang",
        r"koleksi hutang", r"daftar hutang", r"yang punya hutang",
        r"siapa.*punya hutang", r"siapa.*berhutang", r"siapa.*berutang",
        r"list.*hutang.*(?:semua|customer|pelanggan)",
        r"rekap.*hutang", r"semua.*piutang", r"penagihan",
        r"daftar.*(?:bon|piutang)", r"siapa.*(?:ada\s+)?bon",
        r"tampilkan.*(?:hutang|piutang)",
        r"who.*(?:hasn.t|has not|not).*paid", r"who.*owes",
        r"unpaid.*debt", r"debt.*collection", r"outstanding.*debt",
    ]),
    ("record_payment", [
        r"(?<!belum )bayar\s+(?:hutang|utang|piutang)",
        r"lunasi\s+hutang",
        r"pelunasan\s+hutang",
        r"pay(?:s|ing)?\s+(?:debt|the debt)",
        r"paid?\s+(?:debt|hutang)",
        r"debt\s+payment",
    ]),
    ("record_sale", [
        r"\bjual\b", r"terjual", r"catat penjualan", r"catat jualan",
        r"tadi jual",
        r"\bsold\b", r"\bsell\b", r"record\s+(?:a\s+)?sale",
        r"just\s+sold",
    ]),
    ("sales_forecast", [
        r"forecast", r"prediksi", r"perkiraan penjualan",
        r"besok.*(?:ramai|rame|sepi)",
        r"ramai\s+(?:ga|gak|tidak)?\s*besok",
        r"kira.kira.*(?:ramai|rame)",
        r"tomorrow.*(?:busy|quiet)", r"will.*be\s+busy",
    ]),
    ("restock_alert", [
        r"mau habis", r"restock", r"perlu restock", r"stok kritis",
        r"produk apa yang", r"barang apa yang",
        r"running low", r"low stock", r"which products",
        r"need(?:s)? restock",
    ]),
    ("sales_report", [
        r"pendapatan", r"omzet", r"omset", r"penjualan hari",
        r"laporan penjualan", r"berapa jualan", r"total jual",
        r"revenue", r"earnings", r"sales today", r"today.s revenue",
        r"weekly revenue", r"how much.*(?:sold|sales)",
    ]),
    ("check_debt", [
        r"hutang", r"piutang", r"utang", r"belum lunas",
        r"\bdebt\b", r"owes", r"outstanding",
    ]),
    ("check_stock", [
        r"stok", r"stock", r"tinggal berapa", r"ada berapa",
        r"sisa berapa", r"masih ada",
        r"how much.*stock", r"stock.*left",
    ]),
]

KATA_BUKAN_PRODUK = frozenset({
    "berapa", "sisa", "tinggal", "ada", "masih", "min", "max",
})


def normalisasi_teks(pesan: str) -> str:
    """Lowercase dan bersihkan filler umum."""
    teks = pesan.lower().strip()
    for filler in ("bu", "pak", "mbak", "tolong", "dong", "deh", "ya"):
        teks = re.sub(rf"\b{filler}\b", " ", teks)
    return re.sub(r"\s+", " ", teks).strip()


def ekstrak_nama_produk(pesan: str) -> Optional[str]:
    """Ambil kata kunci produk setelah kata stok/stock."""
    teks = normalisasi_teks(pesan)
    for pola in (
        r"how much\s+(.+?)\s+stock(?:\s+is left)?",
        r"stock of\s+(.+?)(?:\?|$)",
        r"stok\s+(.+?)(?:\s+berapa|\?|$)",
        r"stock\s+(.+?)(?:\s+berapa|\?|$)",
        r"tinggal berapa\s+(.+?)(?:\?|$)",
        r"ada berapa\s+(.+?)(?:\?|$)",
    ):
        m = re.search(pola, teks)
        if m:
            nama = m.group(1).strip()
            if nama and nama not in KATA_BUKAN_PRODUK:
                return nama
    return None


def ekstrak_nama_customer(pesan: str) -> Optional[str]:
    """Ambil nama customer setelah kata hutang (untuk check_debt)."""
    teks = normalisasi_teks(pesan)
    if re.search(r"bayar\s+(?:hutang|utang)", teks):
        return None
    for pola in (
        r"hutang\s+(.+?)(?:\?|$|total|berapa)",
        r"debt\s+(?:of\s+|does\s+)?(.+?)(?:\s+have|\?|$)",
        r"how much debt does\s+(.+?)(?:\s+have|\?|$)",
    ):
        m = re.search(pola, teks)
        if m:
            return m.group(1).strip()
    return None


def klasifikasi_intent(pesan: str) -> str:
    """Tentukan intent dari pesan user."""
    teks = normalisasi_teks(pesan)
    if not teks:
        return "unknown"

    for intent, pola_list in POLA_INTENT:
        for pola in pola_list:
            if re.search(pola, teks):
                return intent
    return "unknown"

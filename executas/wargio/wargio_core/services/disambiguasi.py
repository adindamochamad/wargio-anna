"""Penanganan disambiguasi produk/customer — lanjutkan alur setelah user pilih opsi."""

from __future__ import annotations

import re
from typing import Any, Optional

from wargio_core.util.lokalisasi import t


def parse_pilihan_opsi(
    pesan: str,
    daftar_opsi: list[dict[str, Any]],
) -> Optional[int]:
    """
    Parse balasan user: angka (1/2/3) atau nama produk/customer.
    Return indeks opsi (0-based) atau None.
    """
    if not daftar_opsi:
        return None

    teks = pesan.strip().lower().rstrip(".,!?")
    if not teks:
        return None

    cocok_angka = re.match(r"^(\d+)\s*$", teks)
    if cocok_angka:
        indeks = int(cocok_angka.group(1)) - 1
        if 0 <= indeks < len(daftar_opsi):
            return indeks
        return None

    # Exact / contains match pada nama opsi
    for i, opsi in enumerate(daftar_opsi):
        nama = str(opsi.get("name", "")).lower()
        if teks == nama or teks in nama or nama in teks:
            return i

    return None


def format_pesan_pilih_ulang() -> str:
    return t(
        "Pilihan tidak dikenali. Balas angka **1**, **2**, atau **3**, "
        "atau ketik nama produk persis dari daftar.",
        "Choice not recognized. Reply with **1**, **2**, or **3**, "
        "or type the exact product name from the list.",
    )


def ringkas_opsi_produk(produk: dict[str, Any]) -> dict[str, str]:
    """Simpan minimal data opsi di context sesi (JSON-safe)."""
    return {
        "id": str(produk["_id"]),
        "name": str(produk.get("name", "")),
    }

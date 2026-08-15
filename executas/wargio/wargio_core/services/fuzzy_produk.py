"""
Pipeline fuzzy matching produk — Section 6B .cursorules.md.

Urutan: normalisasi → exact alias → partial score → vector search → disambiguasi.

Executa MVP: vector search dinonaktifkan (buat_embedding_teks selalu None).
"""

from __future__ import annotations

import re
from typing import Any, Optional

from pymongo.asynchronous.database import AsyncDatabase

from wargio_core.services.atlas_tools import mcp_find
from wargio_core.services.klasifikasi import normalisasi_teks

NAMA_INDEX_VECTOR = "products_vector_index"
AMBANG_PARTIAL_LANGSUNG = 0.8
AMBANG_PARTIAL_MIN = 0.6
AMBANG_VECTOR_LANGSUNG = 0.85
JARAK_DISAMBIGUASI = 0.15


# --- MVP stub: skip Gemini embedding ---
async def buat_embedding_teks(teks: str) -> Optional[list[float]]:
    """Stub — selalu return None di MVP (skip vector search)."""
    return None


def normalisasi_nama_produk(teks: str) -> str:
    """Langkah 0 — lowercase + hapus filler umum."""
    teks_bersih = re.sub(r"[,!?]+", " ", teks)
    return normalisasi_teks(teks_bersih)


def hitung_skor_partial(teks_cari: str, produk: dict[str, Any]) -> float:
    """Skor kecocokan nama/alias: exact 1.0, prefix 0.8, contains 0.6."""
    if not teks_cari:
        return 0.0

    nama = str(produk.get("name", "")).lower()
    daftar_alias = [str(a).lower() for a in produk.get("name_aliases") or []]

    if teks_cari == nama or teks_cari in daftar_alias:
        skor = 1.0
    elif nama.startswith(teks_cari) or any(a.startswith(teks_cari) for a in daftar_alias):
        skor = 0.8
    elif teks_cari in nama or any(teks_cari in a for a in daftar_alias):
        skor = 0.6
    else:
        skor = 0.0

    # Bonus token ukuran (600ml vs 1.5L) — hindari ambigu palsu
    for token in re.findall(r"\d+(?:\.\d+)?\s*(?:ml|l|kg|g|gr|pcs|bungkus)", teks_cari):
        token_bersih = re.sub(r"\s+", "", token)
        nama_bersih = re.sub(r"\s+", "", nama)
        if token_bersih in nama_bersih:
            skor = max(skor, 0.95)

    return skor


async def _cari_exact(
    db: AsyncDatabase,
    teks: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    pola = f"^{re.escape(teks)}$"
    filter_query = {
        "$or": [
            {"name": {"$regex": pola, "$options": "i"}},
            {"name_aliases": {"$regex": pola, "$options": "i"}},
        ]
    }
    return await mcp_find(db, "products", filter_query, limit=5)


async def _cari_partial_regex(
    db: AsyncDatabase,
    teks: str,
    batas: int = 10,
) -> tuple[list[dict[str, Any]], list[str]]:
    filter_query = {
        "$or": [
            {"name": {"$regex": re.escape(teks), "$options": "i"}},
            {"name_aliases": {"$regex": re.escape(teks), "$options": "i"}},
        ]
    }
    return await mcp_find(db, "products", filter_query, limit=batas)


async def _cari_vector(
    db: AsyncDatabase,
    teks: str,
    batas: int = 5,
) -> tuple[list[tuple[dict[str, Any], float]], list[str]]:
    """Vector search Atlas — butuh field name_embedding terisi."""
    vektor = await buat_embedding_teks(teks)
    if not vektor:
        return [], []

    aksi = ["mcp:aggregate", "vectorSearch"]
    pipeline: list[dict[str, Any]] = [
        {
            "$vectorSearch": {
                "index": NAMA_INDEX_VECTOR,
                "path": "name_embedding",
                "queryVector": vektor,
                "numCandidates": 100,
                "limit": batas,
            }
        },
        {
            "$addFields": {
                "skor_vector": {"$meta": "vectorSearchScore"},
            }
        },
        {
            "$match": {
                "name_embedding": {"$exists": True},
            }
        },
    ]

    try:
        kursor = await db.products.aggregate(pipeline)
        dokumen = await kursor.to_list(length=batas)
    except Exception:
        return [], [*aksi, "vectorSearch:gagal"]

    hasil: list[tuple[dict[str, Any], float]] = []
    for doc in dokumen:
        skor = float(doc.pop("skor_vector", 0.0))
        doc.pop("name_embedding", None)
        hasil.append((doc, skor))
    return hasil, aksi


def _pilih_tunggal_dari_skor(
    terurut: list[tuple[dict[str, Any], float]],
    ambang: float,
) -> Optional[dict[str, Any]]:
    """Satu kandidat jika skor cukup dan tidak ambigu dengan runner-up."""
    if not terurut:
        return None
    terbaik, skor_terbaik = terurut[0]
    if skor_terbaik < ambang:
        return None
    if len(terurut) == 1:
        return terbaik
    _, skor_kedua = terurut[1]
    if skor_terbaik - skor_kedua >= JARAK_DISAMBIGUASI:
        return terbaik
    return None


async def resolve_produk_fuzzy(
    db: AsyncDatabase,
    kata_kunci: Optional[str],
) -> tuple[Optional[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """
    Resolve satu produk via pipeline fuzzy.
    Return (produk, opsi_disambiguasi, aksi_mcp).
    """
    if not kata_kunci:
        return None, [], []

    teks = normalisasi_nama_produk(kata_kunci)
    if not teks:
        return None, [], []

    aksi: list[str] = ["fuzzy:pipeline"]

    # Langkah 1 — exact alias
    exact, aksi_exact = await _cari_exact(db, teks)
    aksi.extend(aksi_exact)
    if len(exact) == 1:
        return exact[0], [], aksi
    if len(exact) > 1:
        return None, exact[:3], [*aksi, "disambiguasi:exact"]

    # Langkah 2 — partial + skor
    partial, aksi_partial = await _cari_partial_regex(db, teks)
    aksi.extend(aksi_partial)
    terurut_partial = sorted(
        ((p, hitung_skor_partial(teks, p)) for p in partial),
        key=lambda x: x[1],
        reverse=True,
    )
    terurut_partial = [(p, s) for p, s in terurut_partial if s >= AMBANG_PARTIAL_MIN]

    pilihan_partial = _pilih_tunggal_dari_skor(terurut_partial, AMBANG_PARTIAL_LANGSUNG)
    if pilihan_partial:
        return pilihan_partial, [], [*aksi, "fuzzy:partial"]

    # Langkah 3 — vector search (disabled in MVP — buat_embedding_teks returns None)
    vector, aksi_vector = await _cari_vector(db, teks)
    aksi.extend(aksi_vector)
    pilihan_vector = _pilih_tunggal_dari_skor(vector, AMBANG_VECTOR_LANGSUNG)
    if pilihan_vector:
        return pilihan_vector, [], [*aksi, "fuzzy:vector"]

    # Langkah 4 — disambiguasi (gabung kandidat partial + vector, unik by _id)
    kandidat: dict[str, tuple[dict[str, Any], float]] = {}
    for produk, skor in terurut_partial:
        kunci = str(produk["_id"])
        if kunci not in kandidat or skor > kandidat[kunci][1]:
            kandidat[kunci] = (produk, skor)
    # Vector lemah (<0.85) tidak masuk disambiguasi — hindari false positive typo random
    for produk, skor in vector:
        if skor < AMBANG_VECTOR_LANGSUNG:
            continue
        kunci = str(produk["_id"])
        if kunci not in kandidat or skor > kandidat[kunci][1]:
            kandidat[kunci] = (produk, skor)

    if not kandidat:
        return None, [], aksi

    terurut_akhir = sorted(kandidat.values(), key=lambda x: x[1], reverse=True)
    if len(terurut_akhir) == 1:
        return terurut_akhir[0][0], [], [*aksi, "fuzzy:satu_kandidat"]

    opsi = [p for p, _ in terurut_akhir[:3]]
    return None, opsi, [*aksi, "disambiguasi:fuzzy"]

"""Koneksi MongoDB Atlas via PyMongo Async API — tanpa pydantic."""

from __future__ import annotations

import os
from typing import Optional

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

_klien: Optional[AsyncMongoClient] = None


async def dapatkan_database() -> AsyncDatabase:
    """
    Mengembalikan database async. Membuat klien sekali per proses.

    Raises:
        RuntimeError: Jika MONGODB_URI belum dikonfigurasi.
    """
    global _klien

    uri = os.environ.get("MONGODB_URI", "").strip()
    database = os.environ.get("MONGODB_DATABASE", "wargio_demo").strip()

    if not uri:
        raise RuntimeError(
            "MONGODB_URI belum diset. Export environment variable dengan connection string Atlas."
        )

    placeholder = ("USER", "PASSWORD", "your_", "changeme")
    if any(p in uri for p in placeholder):
        raise RuntimeError(
            "MONGODB_URI masih berisi placeholder. Ganti dengan connection string Atlas yang valid."
        )

    if _klien is None:
        _klien = AsyncMongoClient(uri)
    return _klien[database]


async def tutup_koneksi() -> None:
    """Menutup klien MongoDB saat shutdown."""
    global _klien
    if _klien is not None:
        await _klien.close()
        _klien = None


async def cek_koneksi_atlas() -> bool:
    """Ping Atlas; False jika gagal atau belum dikonfigurasi."""
    try:
        db = await dapatkan_database()
        await db.command("ping")
        return True
    except Exception:
        return False

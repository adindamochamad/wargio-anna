"""Konfigurasi Wargio Executa — baca dari environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class Pengaturan:
    """Pengaturan runtime — baca dari os.environ (tanpa pydantic)."""

    mongodb_uri: str = field(default_factory=lambda: os.environ.get("MONGODB_URI", ""))
    mongodb_database: str = field(
        default_factory=lambda: os.environ.get("MONGODB_DATABASE", "wargio_demo")
    )

    # MCP tidak digunakan di Executa — selalu False
    mcp_live_enabled: bool = False

    @property
    def atlas_terkonfigurasi(self) -> bool:
        """True jika URI Atlas sudah diisi (bukan placeholder)."""
        uri = self.mongodb_uri.strip()
        if not uri:
            return False
        placeholder = ("USER", "PASSWORD", "your_", "changeme")
        return not any(p in uri for p in placeholder)

    @property
    def gemini_terkonfigurasi(self) -> bool:
        """Selalu False untuk MVP — skip Gemini embeddings."""
        return False


@lru_cache
def ambil_pengaturan() -> Pengaturan:
    """Singleton pengaturan agar tidak baca env berulang."""
    return Pengaturan()

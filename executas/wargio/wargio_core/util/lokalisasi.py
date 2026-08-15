"""Konteks bahasa respons agent — id (default) atau en (judge)."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

VAR_BAHASA: ContextVar[str] = ContextVar("wargio_bahasa", default="id")


def normalisasi_kode_bahasa(kode: str | None) -> str:
    if kode and kode.lower().startswith("en"):
        return "en"
    return "id"


def ambil_bahasa() -> str:
    return VAR_BAHASA.get()


def t(teks_id: str, teks_en: str) -> str:
    """Pilih string sesuai bahasa aktif."""
    return teks_en if ambil_bahasa() == "en" else teks_id


def label_metode_bayar(metode: str) -> str:
    if metode == "hutang":
        return t("hutang", "credit")
    return t("tunai", "cash")


@contextmanager
def konteks_bahasa(kode: str) -> Iterator[None]:
    token = VAR_BAHASA.set(normalisasi_kode_bahasa(kode))
    try:
        yield
    finally:
        VAR_BAHASA.reset(token)

"""Utilitas format angka dan tanggal."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def format_rupiah(jumlah: int | float) -> str:
    """Format angka ke Rupiah Indonesia, contoh: Rp 12.500."""
    bilangan = int(round(jumlah))
    teks = f"{bilangan:,}".replace(",", ".")
    return f"Rp {teks}"


def tanggal_indonesia(dt: datetime | None = None) -> str:
    """Format tanggal Bahasa Indonesia singkat."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_wib = dt.astimezone(ZoneInfo("Asia/Jakarta"))
    nama_hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    nama_bulan = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    ]
    return (
        f"{nama_hari[dt_wib.weekday()]}, {dt_wib.day} "
        f"{nama_bulan[dt_wib.month - 1]} {dt_wib.year}"
    )

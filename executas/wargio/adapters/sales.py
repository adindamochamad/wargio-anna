"""Adapter: get_sales tool → wargio_core intent handlers."""

from __future__ import annotations

from wargio_core.db.koneksi import dapatkan_database
from wargio_core.services.intent_handlers import handle_sales_report
from wargio_core.util.lokalisasi import konteks_bahasa


async def run_get_sales(args: dict) -> dict:
    """Execute get_sales tool and return envelope."""
    period: str = args.get("period", "today")
    language: str = args.get("language", "id")

    with konteks_bahasa(language):
        db = await dapatkan_database()

        if period == "week":
            pesan = "laporan penjualan minggu"
        else:
            pesan = "laporan penjualan hari ini"

        message, actions = await handle_sales_report(db, pesan)

    return {"success": True, "data": {"message": message, "actions": actions}}

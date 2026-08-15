"""Adapter: sales_forecast tool → wargio_core intent handlers."""

from __future__ import annotations

from wargio_core.db.koneksi import dapatkan_database
from wargio_core.services.intent_handlers import handle_sales_forecast
from wargio_core.util.lokalisasi import konteks_bahasa


async def run_sales_forecast(args: dict) -> dict:
    """Execute sales_forecast tool and return envelope."""
    language: str = args.get("language", "id")

    with konteks_bahasa(language):
        db = await dapatkan_database()
        message, actions = await handle_sales_forecast(db)

    return {"success": True, "data": {"message": message, "actions": actions}}

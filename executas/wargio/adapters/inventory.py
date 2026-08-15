"""Adapter: get_inventory tool → wargio_core intent handlers."""

from __future__ import annotations

from wargio_core.db.koneksi import dapatkan_database
from wargio_core.services.intent_handlers import handle_check_stock, handle_restock_alert
from wargio_core.util.lokalisasi import konteks_bahasa


async def run_get_inventory(args: dict) -> dict:
    """Execute get_inventory tool and return envelope."""
    query: str | None = args.get("query")
    low_stock_only: bool = args.get("low_stock_only", False)
    language: str = args.get("language", "id")

    with konteks_bahasa(language):
        db = await dapatkan_database()

        if query:
            pesan = f"stok {query}"
            message, actions = await handle_check_stock(db, pesan)
        elif low_stock_only:
            message, actions = await handle_restock_alert(db)
        else:
            # Default: show restock alert (low stock overview)
            message, actions = await handle_restock_alert(db)

    return {"success": True, "data": {"message": message, "actions": actions}}

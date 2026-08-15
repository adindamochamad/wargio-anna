"""Adapter: get_debts tool → wargio_core intent handlers."""

from __future__ import annotations

from wargio_core.db.koneksi import dapatkan_database
from wargio_core.services.intent_handlers import handle_check_debt, handle_debt_collection
from wargio_core.util.lokalisasi import konteks_bahasa


async def run_get_debts(args: dict) -> dict:
    """Execute get_debts tool and return envelope."""
    customer_name: str | None = args.get("customer_name")
    list_all: bool = args.get("list_all", False)
    language: str = args.get("language", "id")

    with konteks_bahasa(language):
        db = await dapatkan_database()

        if customer_name:
            pesan = f"hutang {customer_name}"
            message, actions = await handle_check_debt(db, pesan)
        elif list_all:
            message, actions = await handle_debt_collection(db)
        else:
            # Default: show all debts overview
            message, actions = await handle_debt_collection(db)

    return {"success": True, "data": {"message": message, "actions": actions}}

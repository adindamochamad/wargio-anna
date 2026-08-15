"""Wargio Executa stdio plugin — tools wired to wargio_core handlers.

Provides: ping, get_inventory, get_sales, get_debts, record_payment.
Each tool dispatches to an adapter that calls vendored wargio_core business logic.
"""

import asyncio
import json
import sys

# Persistent event loop shared by all async tool invocations.
# This avoids AsyncMongoClient being bound to a now-closed loop on subsequent calls.
_loop = asyncio.new_event_loop()

MANIFEST = {
    "name": "tool-dev-wargio",
    "version": "0.1.0",
    "tools": [
        {
            "name": "ping",
            "description": "Smoke-test method. Returns pong.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        {
            "name": "get_inventory",
            "description": "Check product stock levels or list low-stock items needing restock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Product name to check specific stock level.",
                    },
                    "low_stock_only": {
                        "type": "boolean",
                        "default": False,
                        "description": "If true, only return products at or below minimum stock.",
                    },
                    "language": {
                        "type": "string",
                        "enum": ["id", "en"],
                        "default": "id",
                        "description": "Response language: 'id' (Indonesian) or 'en' (English).",
                    },
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "get_sales",
            "description": "Get sales report for today or the past week.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["today", "week"],
                        "default": "today",
                        "description": "Report period: 'today' or 'week'.",
                    },
                    "language": {
                        "type": "string",
                        "enum": ["id", "en"],
                        "default": "id",
                        "description": "Response language: 'id' (Indonesian) or 'en' (English).",
                    },
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "get_debts",
            "description": "Check a specific customer's debt or list all customers with outstanding debt.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Customer name to check specific debt.",
                    },
                    "list_all": {
                        "type": "boolean",
                        "default": False,
                        "description": "If true, list all customers with outstanding debt.",
                    },
                    "language": {
                        "type": "string",
                        "enum": ["id", "en"],
                        "default": "id",
                        "description": "Response language: 'id' (Indonesian) or 'en' (English).",
                    },
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "record_payment",
            "description": "Record a customer debt payment. Use action='prepare' first to get a draft summary, then action='confirm' with the draft_id to execute the write, or action='cancel' to discard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["prepare", "confirm", "cancel"],
                        "description": "Phase: 'prepare' validates and creates draft, 'confirm' executes write, 'cancel' discards draft.",
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Customer name (required for prepare).",
                    },
                    "amount": {
                        "type": "number",
                        "description": "Payment amount in IDR (required for prepare).",
                    },
                    "draft_id": {
                        "type": "string",
                        "description": "Draft ID from prepare response (required for confirm/cancel).",
                    },
                    "language": {
                        "type": "string",
                        "enum": ["id", "en"],
                        "default": "id",
                        "description": "Response language: 'id' (Indonesian) or 'en' (English).",
                    },
                },
                "required": ["action"],
                "additionalProperties": False,
            },
        },
    ],
}


def invoke(method: str, args: dict) -> dict:
    """Dispatch tool invocation. Returns envelope dict.

    Async adapters are executed via asyncio.run() since the stdio loop is sync.
    """
    if method == "ping":
        return {"success": True, "data": {"pong": True}}

    if method == "get_inventory":
        try:
            from adapters.inventory import run_get_inventory

            return _loop.run_until_complete(run_get_inventory(args))
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": str(e)}

    if method == "get_sales":
        try:
            from adapters.sales import run_get_sales

            return _loop.run_until_complete(run_get_sales(args))
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": str(e)}

    if method == "get_debts":
        try:
            from adapters.debts import run_get_debts

            return _loop.run_until_complete(run_get_debts(args))
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": str(e)}

    if method == "record_payment":
        try:
            from adapters.payment import run_record_payment

            return _loop.run_until_complete(run_record_payment(args))
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": str(e)}

    return {"success": False, "error": f"unknown method: {method}"}


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        try:
            if req.get("method") == "describe":
                result = MANIFEST
            elif req.get("method") == "health":
                result = {"status": "ok"}
            elif req.get("method") == "invoke":
                result = invoke(req["params"]["tool"], req["params"].get("arguments", {}))
            else:
                raise ValueError(f"unknown rpc: {req.get('method')}")
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": req.get("id"), "result": result}) + "\n")
        except Exception as e:  # noqa: BLE001
            sys.stdout.write(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": req.get("id"),
                        "error": {"code": -32601, "message": str(e)},
                    }
                )
                + "\n"
            )
        sys.stdout.flush()


if __name__ == "__main__":
    main()

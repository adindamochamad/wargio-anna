#!/usr/bin/env python3
"""Standalone smoke test for Wargio Executa plugin.

Exercises all 5 tool methods (ping, get_inventory, get_sales, get_debts, record_payment)
via the stdio JSON-RPC interface. Requires:
  - pymongo installed in executas/wargio/.venv
  - MONGODB_URI and MONGODB_DATABASE set (or .env at project root)

Usage:
    python scripts/smoke_test_executa.py           # full test (needs DB)
    python scripts/smoke_test_executa.py --offline  # describe/health/ping only
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "executas" / "wargio"
PYTHON = str(PLUGIN_DIR / ".venv" / "bin" / "python")
PLUGIN = str(PLUGIN_DIR / "wargio_plugin.py")

# Load .env for subprocess
ENV_FILE = ROOT / ".env"


def load_env_dict() -> dict[str, str]:
    """Parse .env file into dict (simple key=value, skip comments)."""
    import os
    env = dict(os.environ)
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


class ExecuaClient:
    """Simple JSON-RPC client over stdio."""

    def __init__(self, offline: bool = False):
        self.offline = offline
        env = load_env_dict()
        if offline:
            env.pop("MONGODB_URI", None)
        self.proc = subprocess.Popen(
            [PYTHON, PLUGIN],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(PLUGIN_DIR),
            env=env,
        )
        self._id = 0

    def call(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        req = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params:
            req["params"] = params
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError("No response from plugin (process may have crashed)")
        return json.loads(line)

    def invoke(self, tool: str, arguments: dict | None = None) -> dict:
        return self.call("invoke", {"tool": tool, "arguments": arguments or {}})

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=5)


def test_describe(client: ExecuaClient) -> None:
    resp = client.call("describe")
    result = resp["result"]
    assert result["name"] == "tool-dev-wargio", f"Unexpected name: {result['name']}"
    tools = [t["name"] for t in result["tools"]]
    expected = {"ping", "get_inventory", "get_sales", "get_debts", "record_payment"}
    assert expected.issubset(set(tools)), f"Missing tools: {expected - set(tools)}"
    print(f"  ✓ describe: {len(result['tools'])} tools registered")


def test_health(client: ExecuaClient) -> None:
    resp = client.call("health")
    assert resp["result"]["status"] == "ok"
    print("  ✓ health: ok")


def test_ping(client: ExecuaClient) -> None:
    resp = client.invoke("ping")
    assert resp["result"]["success"] is True
    assert resp["result"]["data"]["pong"] is True
    print("  ✓ ping: pong")


def test_get_inventory(client: ExecuaClient) -> None:
    # Restock alert
    resp = client.invoke("get_inventory", {"low_stock_only": True, "language": "id"})
    result = resp["result"]
    assert result["success"] is True, f"Failed: {result.get('error')}"
    assert "message" in result["data"]
    print(f"  ✓ get_inventory (restock): {len(result['data']['message'])} chars")

    # Specific product
    resp = client.invoke("get_inventory", {"query": "aqua", "language": "en"})
    result = resp["result"]
    assert result["success"] is True, f"Failed: {result.get('error')}"
    print(f"  ✓ get_inventory (query=aqua): ok")


def test_get_sales(client: ExecuaClient) -> None:
    resp = client.invoke("get_sales", {"period": "today", "language": "id"})
    result = resp["result"]
    assert result["success"] is True, f"Failed: {result.get('error')}"
    print(f"  ✓ get_sales (today): ok")

    resp = client.invoke("get_sales", {"period": "week", "language": "en"})
    result = resp["result"]
    assert result["success"] is True, f"Failed: {result.get('error')}"
    print(f"  ✓ get_sales (week): ok")


def test_get_debts(client: ExecuaClient) -> None:
    resp = client.invoke("get_debts", {"list_all": True, "language": "id"})
    result = resp["result"]
    assert result["success"] is True, f"Failed: {result.get('error')}"
    print(f"  ✓ get_debts (list_all): ok")

    resp = client.invoke("get_debts", {"customer_name": "Bu Sari", "language": "id"})
    result = resp["result"]
    assert result["success"] is True, f"Failed: {result.get('error')}"
    print(f"  ✓ get_debts (Bu Sari): ok")


def test_record_payment(client: ExecuaClient) -> None:
    # Prepare
    resp = client.invoke("record_payment", {
        "action": "prepare",
        "customer_name": "Pak Agus",
        "amount": 10000,
        "language": "id",
    })
    result = resp["result"]
    assert result["success"] is True, f"Prepare failed: {result.get('error')}"
    draft_id = result["data"]["draft_id"]
    assert result["data"]["requires_confirmation"] is True
    print(f"  ✓ record_payment (prepare): draft_id={draft_id[:8]}...")

    # Cancel (don't actually write to DB in smoke test)
    resp = client.invoke("record_payment", {
        "action": "cancel",
        "draft_id": draft_id,
        "language": "id",
    })
    result = resp["result"]
    assert result["success"] is True
    assert result["data"]["cancelled"] is True
    print(f"  ✓ record_payment (cancel): draft removed")

    # Confirm expired/cancelled
    resp = client.invoke("record_payment", {
        "action": "confirm",
        "draft_id": draft_id,
        "language": "id",
    })
    result = resp["result"]
    assert result["success"] is False
    print(f"  ✓ record_payment (confirm cancelled): properly rejected")

    # Error: invalid customer
    resp = client.invoke("record_payment", {
        "action": "prepare",
        "customer_name": "Nobody",
        "amount": 5000,
        "language": "en",
    })
    result = resp["result"]
    assert result["success"] is False
    assert "not found" in result["error"].lower()
    print(f"  ✓ record_payment (invalid customer): error returned")


def main() -> None:
    offline = "--offline" in sys.argv

    print(f"\n{'='*50}")
    print(f"  Wargio Executa Smoke Test {'(offline)' if offline else '(full)'}")
    print(f"{'='*50}\n")

    client = ExecuaClient(offline=offline)

    try:
        # Always test these (no DB needed)
        test_describe(client)
        test_health(client)
        test_ping(client)

        if not offline:
            test_get_inventory(client)
            test_get_sales(client)
            test_get_debts(client)
            test_record_payment(client)
        else:
            print("\n  [offline mode — skipping DB-dependent tests]")

    except AssertionError as e:
        print(f"\n  ✗ FAILED: {e}")
        client.close()
        sys.exit(1)
    except Exception as e:
        print(f"\n  ✗ ERROR: {type(e).__name__}: {e}")
        client.close()
        sys.exit(1)

    client.close()

    n_tests = 3 if offline else 13
    print(f"\n{'='*50}")
    print(f"  ✓ ALL {n_tests} TESTS PASSED")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()

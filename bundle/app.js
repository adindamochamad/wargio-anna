// Wargio Anna App — Dashboard with tool invocations
import { AnnaAppRuntime } from "/static/anna-apps/_sdk/latest/index.js";

const TOOL_ID = "tool-dev-wargio";
let anna = null;

async function callTool(method, args = {}) {
  if (!anna) return { success: false, error: "Not connected" };
  try {
    return await anna.tools.invoke({ tool_id: TOOL_ID, method, args });
  } catch (e) {
    return { success: false, error: e.message };
  }
}

function renderResult(elementId, result) {
  const el = document.getElementById(elementId);
  if (!el) return;
  if (result.success) {
    el.textContent = result.data?.message || JSON.stringify(result.data);
  } else {
    el.textContent = "Error: " + (result.error || "unknown");
  }
}

async function refreshInventory() {
  const el = document.getElementById("inventory-body");
  if (el) el.textContent = "Memuat...";
  const result = await callTool("get_inventory", { low_stock_only: true });
  renderResult("inventory-body", result);
}

async function refreshSales() {
  const el = document.getElementById("sales-body");
  if (el) el.textContent = "Memuat...";
  const result = await callTool("get_sales", { period: "today" });
  renderResult("sales-body", result);
}

async function refreshDebts() {
  const el = document.getElementById("debts-body");
  if (el) el.textContent = "Memuat...";
  const result = await callTool("get_debts", { list_all: true });
  renderResult("debts-body", result);
}

async function main() {
  try {
    anna = await AnnaAppRuntime.connect();
    await anna.window.set_title({ title: "Wargio Dashboard" });
  } catch (e) {
    // Standalone preview mode
    document.querySelectorAll(".card-body").forEach((el) => {
      el.textContent = "Preview mode (no host)";
    });
    return;
  }

  // Wire refresh buttons
  document.getElementById("btn-inventory")?.addEventListener("click", refreshInventory);
  document.getElementById("btn-sales")?.addEventListener("click", refreshSales);
  document.getElementById("btn-debts")?.addEventListener("click", refreshDebts);

  // Initial load
  await Promise.allSettled([refreshInventory(), refreshSales(), refreshDebts()]);
}

main();

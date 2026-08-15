// Wargio Anna App bundle entry (Gelombang 0 ping/pong harness).
// Real dashboard cards (inventory / sales / debts) are wired in later waves.
import { AnnaAppRuntime } from "/static/anna-apps/_sdk/latest/index.js";

const TOOL_ID = "tool-dev-wargio";

async function main() {
  const status = document.getElementById("status");
  const btn = document.getElementById("primary-btn");
  if (!status || !btn) return;

  let anna;
  try {
    anna = await AnnaAppRuntime.connect();
  } catch (e) {
    status.textContent = "Standalone preview (no host).";
    return;
  }

  await anna.window.set_title({ title: "Wargio" });
  status.textContent = "Ready.";

  btn.addEventListener("click", async () => {
    status.textContent = "Running…";
    try {
      const out = await anna.tools.invoke({
        tool_id: TOOL_ID,
        method: "ping",
        args: {},
      });
      await anna.storage.set({ key: "wargio:last_ping", value: Date.now() });
      status.textContent = JSON.stringify(out, null, 2);
    } catch (e) {
      status.textContent = "Error: " + e.message;
    }
  });
}

main();

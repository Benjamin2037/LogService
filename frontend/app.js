const chat = document.getElementById("chat");
const statusEl = document.getElementById("status");

function appendMessage(type, title, content) {
  const msg = document.createElement("div");
  msg.className = `message ${type}`;
  msg.innerHTML = `<strong>${title}</strong>${content ? `<pre>${content}</pre>` : ""}`;
  chat.appendChild(msg);
  msg.scrollIntoView({ behavior: "smooth", block: "end" });
}

function readInputs() {
  const components = document.getElementById("components").value
    .split(",")
    .map((c) => c.trim())
    .filter(Boolean);
  const keywords = document.getElementById("keywords").value
    .split(",")
    .map((k) => k.trim())
    .filter(Boolean);

  return {
    cluster_id: document.getElementById("clusterId").value.trim(),
    cluster_config_path: document.getElementById("configPath").value.trim() || null,
    components,
    keywords,
    time_range: {
      start: document.getElementById("startTime").value.trim(),
      end: document.getElementById("endTime").value.trim(),
    },
    max_lines: 100,
    window_seconds: 300,
  };
}

async function runQuery() {
  const payload = readInputs();
  appendMessage("user", "Query", JSON.stringify(payload, null, 2));
  statusEl.textContent = "running";

  try {
    const res = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(text);
    }

    const data = await res.json();
    const lines = data.lines
      .map((line) => `${line.ts} ${line.line}`)
      .join("\n");
    appendMessage("system", "Results", lines || "(no lines)");
  } catch (err) {
    appendMessage("system", "Error", err.message || "request failed");
  } finally {
    statusEl.textContent = "idle";
  }
}

async function exportText() {
  appendMessage("user", "Export", "Requesting export...");
  statusEl.textContent = "exporting";

  const lastSystem = Array.from(document.querySelectorAll(".message.system pre")).pop();
  const lines = lastSystem
    ? lastSystem.textContent.split("\n").map((line) => ({ ts: "", line, labels: {} }))
    : [];

  try {
    const res = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ format: "text", lines }),
    });
    const data = await res.json();
    appendMessage("system", "Exported", data.path);
  } catch (err) {
    appendMessage("system", "Export Error", err.message || "export failed");
  } finally {
    statusEl.textContent = "idle";
  }
}

document.getElementById("runQuery").addEventListener("click", runQuery);
document.getElementById("exportText").addEventListener("click", exportText);

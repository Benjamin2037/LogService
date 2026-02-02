const chat = document.getElementById("chat");
const statusEl = document.getElementById("status");
const timelineWindow = document.getElementById("timelineWindow");

function clearEmptyState() {
  const empty = chat.querySelector(".empty-state");
  if (empty) {
    empty.remove();
  }
}

function appendMessage(type, title, content) {
  clearEmptyState();
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

function setStatus(value) {
  statusEl.textContent = value;
}

function appendToInput(id, value) {
  const input = document.getElementById(id);
  const parts = input.value
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);
  if (!parts.includes(value)) {
    parts.push(value);
  }
  input.value = parts.join(",");
}

function setRelativeRange(minutes) {
  const end = new Date();
  const start = new Date(end.getTime() - minutes * 60 * 1000);
  document.getElementById("endTime").value = end.toISOString();
  document.getElementById("startTime").value = start.toISOString();
  renderWindow(minutes / 60 * 100);
}

function renderWindow(widthPercent) {
  timelineWindow.style.width = `${Math.min(60, Math.max(15, widthPercent))}%`;
}

function setEventWindow(iso) {
  const end = new Date(iso);
  const start = new Date(end.getTime() - 10 * 60 * 1000);
  document.getElementById("endTime").value = end.toISOString();
  document.getElementById("startTime").value = start.toISOString();
  renderWindow(25);
}

async function runQuery() {
  const payload = readInputs();
  appendMessage("user", "Query", JSON.stringify(payload, null, 2));
  setStatus("running");

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
    setStatus("idle");
  }
}

async function exportText() {
  appendMessage("user", "Export", "Requesting export...");
  setStatus("exporting");

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
    setStatus("idle");
  }
}

document.getElementById("runQuery").addEventListener("click", runQuery);
document.getElementById("exportText").addEventListener("click", exportText);

document.querySelectorAll("[data-component]").forEach((chip) => {
  chip.addEventListener("click", () => {
    appendToInput("components", chip.dataset.component);
  });
});

document.querySelectorAll("[data-keyword]").forEach((chip) => {
  chip.addEventListener("click", () => {
    appendToInput("keywords", chip.dataset.keyword);
  });
});

document.querySelectorAll("[data-range]").forEach((chip) => {
  chip.addEventListener("click", () => {
    const minutes = Number(chip.dataset.range || 0);
    if (minutes > 0) {
      setRelativeRange(minutes);
    }
  });
});

document.querySelectorAll("[data-event]").forEach((eventBtn) => {
  eventBtn.addEventListener("click", () => {
    setEventWindow(eventBtn.dataset.event);
  });
});

renderWindow(25);

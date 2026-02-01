console.log("PyCells API loaded");


const statusEl = document.getElementById("status");
const uptimeEl = document.getElementById("uptime");

function setStatus(ok, text) {
  statusEl.textContent = text;
  statusEl.className = "status " + (ok ? "ok" : "error");
}

function formatUptime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h}h ${m}m ${s}s`;
}

fetch("/health")
  .then(r => {
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  })
  .then(data => {
    const ok = data.status === "ok";
    setStatus(ok, ok ? "API is running" : "API degraded");

    if (typeof data.uptime_sec === "number") {
      uptimeEl.textContent = formatUptime(data.uptime_sec);
    }

    console.log("Health:", data);
  })
  .catch(err => {
    setStatus(false, "API unreachable");
    uptimeEl.textContent = "—";
    console.error(err);
  });

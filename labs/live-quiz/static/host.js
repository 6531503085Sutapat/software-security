function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function initHost(pin) {
  const socket = io();
  socket.on("connect", () => socket.emit("host_join", { pin }));

  document.getElementById("next-btn").addEventListener("click", () => {
    document.getElementById("results-area").innerHTML = "";
    socket.emit("host_next", { pin });
  });

  socket.on("question:show", (data) => {
    const el = document.getElementById("question-area");
    el.innerHTML = `<h2>${escapeHtml(data.stem)}</h2><p>Question ${data.index + 1} of ${data.total} — ${data.time_limit}s</p>`;
  });

  socket.on("question:results", (data) => {
    const el = document.getElementById("results-area");
    const bars = data.distribution
      .map((count, i) => `<div>Option ${i + 1}: ${count} answer(s)</div>`)
      .join("");
    const board = data.leaderboard
      .map((p, i) => `<li>${i + 1}. ${escapeHtml(p.nickname)} — ${p.score}</li>`)
      .join("");
    el.innerHTML = `<h3>Results</h3>${bars}<h3>Leaderboard</h3><ol>${board}</ol>`;
  });

  socket.on("game:finished", (data) => {
    const board = data.leaderboard
      .map((p, i) => `<li>${i + 1}. ${escapeHtml(p.nickname)} — ${p.score}</li>`)
      .join("");
    document.getElementById("question-area").innerHTML = "<h2>Final results</h2>";
    document.getElementById("results-area").innerHTML = `<ol>${board}</ol>`;
  });
}

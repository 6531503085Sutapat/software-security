const socket = io();
let currentPin = null;
let currentNickname = null;

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

document.getElementById("join-btn").addEventListener("click", () => {
  currentPin = document.getElementById("pin-input").value.trim();
  currentNickname = document.getElementById("nickname-input").value.trim();
  socket.emit("player_join", { pin: currentPin, nickname: currentNickname });
});

socket.on("join_ok", () => {
  document.getElementById("join-area").style.display = "none";
  document.getElementById("game-area").style.display = "block";
});

socket.on("join_error", (data) => {
  document.getElementById("join-error").textContent = data.message;
});

socket.on("question:show", (data) => {
  document.getElementById("feedback-area").innerHTML = "";
  document.getElementById("leaderboard-area").innerHTML = "";
  const el = document.getElementById("question-area");
  el.innerHTML = `<h2>${escapeHtml(data.stem)}</h2>` +
    data.options
      .map((opt, i) => `<button class="answer-btn" data-choice="${i}">${escapeHtml(opt)}</button>`)
      .join("");
  el.querySelectorAll(".answer-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      el.querySelectorAll(".answer-btn").forEach((b) => (b.disabled = true));
      socket.emit("answer_submit", {
        pin: currentPin,
        nickname: currentNickname,
        choice: parseInt(btn.dataset.choice, 10),
      });
    });
  });
});

socket.on("answer:feedback", (data) => {
  document.getElementById("feedback-area").textContent = data.correct
    ? `Correct! +${data.points} points`
    : "Wrong answer — 0 points";
});

socket.on("question:results", (data) => {
  const board = data.leaderboard
    .map((p, i) => `<li>${i + 1}. ${escapeHtml(p.nickname)} — ${p.score}</li>`)
    .join("");
  document.getElementById("leaderboard-area").innerHTML = `<h3>Leaderboard</h3><ol>${board}</ol>`;
});

socket.on("game:finished", (data) => {
  const board = data.leaderboard
    .map((p, i) => `<li>${i + 1}. ${escapeHtml(p.nickname)} — ${p.score}</li>`)
    .join("");
  document.getElementById("question-area").innerHTML = "<h2>Game over!</h2>";
  document.getElementById("leaderboard-area").innerHTML = `<ol>${board}</ol>`;
});

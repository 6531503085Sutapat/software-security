/* Player (phone) screen logic. The server is authoritative for scoring/timing —
   the countdown here is display-only. Personal correct/wrong feedback is held
   until the room-wide reveal so a fast finisher can't shout the answer.
   Every string interpolated into innerHTML goes through esc(). */

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

const OPT_META = [
  { key: "red",    varName: "--a-red",    shape: "s-tri", label: "Triangle · Red" },
  { key: "blue",   varName: "--a-blue",   shape: "s-dia", label: "Diamond · Blue" },
  { key: "yellow", varName: "--a-yellow", shape: "s-cir", label: "Circle · Yellow" },
  { key: "green",  varName: "--a-green",  shape: "s-sq",  label: "Square · Green" },
];

const $ = (id) => document.getElementById(id);
const socket = io();

let pin = null;
let nickname = null;
let joined = false;
let score = 0;
let answered = false;
let pickedIndex = null;
let pendingFeedback = null; // held until question:results
let timerHandle = null;

// ---- join ----
$("join-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const p = $("pin-input").value.trim();
  const n = $("nickname-input").value.trim();
  if (!/^\d{6}$/.test(p)) { $("join-error").textContent = "PIN is the 6-digit code on the big screen."; return; }
  if (!n) { $("join-error").textContent = "Pick a nickname (not your real name)."; return; }
  $("join-error").textContent = "";
  pin = p; nickname = n;
  socket.emit("player_join", { pin, nickname });
});

socket.on("join_ok", () => {
  joined = true;
  $("join").hidden = true;
  $("game").hidden = false;
  $("p-name").textContent = nickname;
  $("p-av").textContent = nickname[0] || "?";
  $("p-wait-big").textContent = "You’re in!";
  $("p-wait-sub").textContent = "Watch the big screen — the first question is coming.";
});

socket.on("join_error", (data) => {
  $("join-error").textContent = data.message;
});

// resume the same identity (and score) after a dropped connection
socket.on("connect", () => {
  if (joined) socket.emit("player_join", { pin, nickname });
});
socket.on("disconnect", () => showNetbar("Reconnecting…"));
socket.io.on("reconnect", () => hideNetbar());

// ---- countdown (display-only) ----
function startTimer(seconds) {
  stopTimer();
  const t0 = Date.now();
  const wrap = $("p-timer");
  wrap.classList.remove("low");
  timerHandle = setInterval(() => {
    const remaining = Math.max(0, seconds - (Date.now() - t0) / 1000);
    $("p-timer-sec").textContent = Math.ceil(remaining);
    $("p-timer-fill").style.width = (remaining / seconds) * 100 + "%";
    if (remaining <= 5) wrap.classList.add("low");
    if (remaining <= 0) stopTimer();
  }, 100);
}
function stopTimer() {
  if (timerHandle) { clearInterval(timerHandle); timerHandle = null; }
}

// ---- question ----
socket.on("question:show", (data) => {
  answered = false;
  pickedIndex = null;
  pendingFeedback = null;

  $("p-wait").hidden = true;
  $("p-feedback").hidden = true;
  $("p-board").hidden = true;
  $("p-lock").hidden = true;
  $("p-question").hidden = false;

  $("p-qnum").textContent = data.index + 1;
  $("p-qtotal").textContent = data.total;
  $("p-stem").textContent = data.stem;

  $("p-tiles").innerHTML = data.options.map((opt, i) => {
    const m = OPT_META[i];
    return `
      <button class="ptile ${m.key}" style="--o:var(${m.varName})" data-choice="${i}"
              aria-label="${esc(opt)} — ${m.label}">
        <svg class="pglyph" aria-hidden="true"><use href="#${m.shape}"/></svg>
        <span class="pl">${esc(opt)}</span>
      </button>`;
  }).join("");

  $("p-tiles").querySelectorAll(".ptile").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (answered) return;
      answered = true;
      pickedIndex = parseInt(btn.dataset.choice, 10);
      $("p-tiles").querySelectorAll(".ptile").forEach((b) => {
        b.disabled = true;
        b.classList.toggle("picked", b === btn);
        b.classList.toggle("dim", b !== btn);
      });
      $("p-lock").hidden = false;
      socket.emit("answer_submit", { pin, nickname, choice: pickedIndex });
    });
  });

  startTimer(data.time_limit);
});

// personal result arrives immediately but is only shown at the reveal
socket.on("answer:feedback", (data) => {
  pendingFeedback = data;
});

// ---- reveal ----
socket.on("question:results", (data) => {
  stopTimer();
  $("p-lock").hidden = true;

  // mark the correct tile; dim the rest
  if (data.correct != null) {
    $("p-tiles").querySelectorAll(".ptile").forEach((b) => {
      const i = parseInt(b.dataset.choice, 10);
      b.disabled = true;
      b.classList.toggle("reveal-correct", i === data.correct);
      b.classList.toggle("dim", i !== data.correct);
    });
  }

  const fb = $("p-feedback");
  fb.hidden = false;
  if (pendingFeedback) {
    score += pendingFeedback.points;
    $("p-score").textContent = score.toLocaleString();
    fb.className = "pfeedback " + (pendingFeedback.correct ? "good" : "bad");
    fb.innerHTML = pendingFeedback.correct
      ? `Correct! +${pendingFeedback.points.toLocaleString()}<span class="sub">Speed counts — nice.</span>`
      : `Not this time +0<span class="sub">The highlighted tile was the answer.</span>`;
  } else if (answered) {
    fb.className = "pfeedback bad";
    fb.textContent = "Answer received…";
  } else {
    fb.className = "pfeedback bad";
    fb.innerHTML = `Time’s up — no answer<span class="sub">Get ready for the next one!</span>`;
  }

  renderBoard(data.leaderboard, false);
});

// ---- finished ----
socket.on("game:finished", (data) => {
  stopTimer();
  $("p-question").hidden = true;
  $("p-feedback").hidden = true;
  $("p-lock").hidden = true;
  $("p-wait").hidden = false;

  const board = data.leaderboard; // full ranking at game end
  const myRank = board.findIndex((p) => p.nickname === nickname) + 1;
  if (myRank > 0) {
    const suffix = ["th", "st", "nd", "rd"][(myRank % 10 <= 3 && Math.floor(myRank % 100 / 10) !== 1) ? myRank % 10 : 0];
    $("p-rank").textContent = myRank + suffix;
    $("p-rank").hidden = false;
    $("p-wait-big").textContent = myRank === 1 ? "🏆 You won!" : `You finished ${myRank}${suffix}`;
  } else {
    $("p-wait-big").textContent = "Game over!";
  }
  $("p-wait-sub").textContent = `Final score: ${score.toLocaleString()} pts`;

  renderBoard(board.slice(0, 5), true);
});

function renderBoard(rows, final) {
  const b = $("p-board");
  b.hidden = false;
  b.innerHTML = `
    <div class="col-h"><span>${final ? "Final leaderboard" : "Leaderboard"}</span><span class="accent">Top 5</span></div>
    <div class="lb">` +
    rows.map((p, i) => `
      <div class="lrow${i === 0 ? " first" : ""}">
        <span class="rk">${i + 1}</span><span class="nm">${esc(p.nickname)}</span>
        <span class="pts">${p.score.toLocaleString()}</span>
      </div>`).join("") +
    `</div>`;
}

// ---- tiny reconnect banner ----
let netbar = null;
function showNetbar(msg) {
  if (!netbar) {
    netbar = document.createElement("div");
    netbar.className = "netbar";
    document.body.appendChild(netbar);
  }
  netbar.textContent = msg;
}
function hideNetbar() {
  if (netbar) { netbar.remove(); netbar = null; }
}

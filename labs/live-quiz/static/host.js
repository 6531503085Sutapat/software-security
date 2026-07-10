/* Host (projector) screen logic. Server is authoritative for all game state;
   this file only renders it. Every string interpolated into innerHTML goes
   through esc() — nicknames and item-bank text are untrusted. */

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

// Answer identity by option index: color + shape + spoken name (never color alone).
const OPT_META = [
  { key: "red",    varName: "--a-red",    shape: "s-tri", label: "Triangle · Red" },
  { key: "blue",   varName: "--a-blue",   shape: "s-dia", label: "Diamond · Blue" },
  { key: "yellow", varName: "--a-yellow", shape: "s-cir", label: "Circle · Yellow" },
  { key: "green",  varName: "--a-green",  shape: "s-sq",  label: "Square · Green" },
];

const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const ARC_LEN = 276.46; // 2πr for r=44

function initHost(pin) {
  const $ = (id) => document.getElementById(id);
  const socket = io();

  let started = false;
  let lastQuestion = null; // {options, index, total}
  let timerHandle = null;

  socket.on("connect", () => socket.emit("host_join", { pin })); // also re-joins the room after a reconnect

  $("join-url").textContent = window.location.host;

  // ---- view switching ----
  function show(view) {
    ["lobby", "question", "results", "finished"].forEach((v) => {
      $(v).hidden = v !== view;
    });
    const labels = { lobby: "Lobby", question: "Live", results: "Reveal", finished: "Finished" };
    $("live-label").textContent = labels[view];
  }

  // ---- next button state machine ----
  const nextBtn = $("next-btn");
  function setNext(label, enabled, hint) {
    nextBtn.textContent = label;
    nextBtn.disabled = !enabled;
    $("foot-hint").textContent = hint || "";
  }
  nextBtn.addEventListener("click", () => {
    nextBtn.disabled = true; // re-enabled by question:show / results; guards double-clicks skipping a question
    socket.emit("host_next", { pin });
  });

  // ---- lobby ----
  socket.on("lobby:update", (data) => {
    if (started) return;
    $("lobby-count").textContent = data.count;
    $("roster").innerHTML = data.players
      .map((n) => `<span class="chip">${esc(n)}</span>`)
      .join("");
    if (data.count > 0) setNext("Start game ▸", true, "Start when everyone’s in");
  });

  // ---- countdown ----
  function startTimer(seconds) {
    stopTimer();
    const t0 = Date.now();
    $("timer-of").textContent = seconds;
    const arc = $("timer-arc");
    const timerEl = $("timer");
    timerEl.classList.remove("low");
    // under reduced-motion the ring steps in whole seconds instead of sweeping continuously
    timerHandle = setInterval(() => {
      const raw = Math.max(0, seconds - (Date.now() - t0) / 1000);
      const shown = Math.ceil(raw);
      $("timer-sec").textContent = shown;
      const frac = REDUCED_MOTION ? shown : raw;
      arc.style.strokeDashoffset = ARC_LEN * (1 - frac / seconds);
      if (raw <= 5) timerEl.classList.add("low");
      if (raw <= 0) stopTimer();
    }, REDUCED_MOTION ? 250 : 100);
  }
  function stopTimer() {
    if (timerHandle) { clearInterval(timerHandle); timerHandle = null; }
  }

  // ---- question ----
  socket.on("question:show", (data) => {
    started = true;
    lastQuestion = data;
    show("question");

    $("q-num").textContent = data.index + 1;
    $("q-total").textContent = data.total;
    $("segs").innerHTML = Array.from({ length: data.total }, (_, i) =>
      `<i class="${i < data.index ? "on" : i === data.index ? "cur" : ""}"></i>`
    ).join("");

    $("answered-n").textContent = "0";
    $("answered-l").textContent = `of ${data.players} answered`;
    $("stem").textContent = data.stem;

    $("answers").innerHTML = data.options.map((opt, i) => {
      const m = OPT_META[i];
      return `
        <div class="opt ${m.key}" style="--o:var(${m.varName})">
          <div class="band"><svg class="glyph" aria-hidden="true"><use href="#${m.shape}"/></svg></div>
          <div class="body"><div class="otag">${m.label}</div><div class="otxt">${esc(opt)}</div></div>
          <div class="ghost" aria-hidden="true">${"ABCD"[i]}</div>
        </div>`;
    }).join("");

    startTimer(data.time_limit);
    setNext("Question in progress…", false, "Results appear when everyone answers or time runs out");
  });

  socket.on("answer:tally", (data) => {
    $("answered-n").textContent = data.answered;
    $("answered-l").textContent = `of ${data.total} answered`;
  });

  // ---- results ----
  socket.on("question:results", (data) => {
    stopTimer();
    show("results");

    const q = lastQuestion || { options: [], index: 0, total: 0 };
    const total = data.distribution.reduce((a, b) => a + b, 0);
    const max = Math.max(1, ...data.distribution);

    if (data.correct != null && q.options[data.correct] != null) {
      const m = OPT_META[data.correct];
      $("reveal").innerHTML = `
        <svg class="rglyph" style="--o:var(${m.varName})" aria-hidden="true"><use href="#${m.shape}"/></svg>
        <div class="rb-txt">
          <div class="rb-k">Correct answer · Question ${q.index + 1} / ${q.total}</div>
          <div class="rb-a">${esc(q.options[data.correct])}</div>
        </div>
        <div class="rb-pill"><svg class="ck"><use href="#s-ck"/></svg><span class="lab">Correct</span></div>`;
    }

    $("resp-count").textContent = `${total} response${total === 1 ? "" : "s"}`;
    $("bars").innerHTML = data.distribution.map((count, i) => {
      const m = OPT_META[i];
      const isCorrect = i === data.correct;
      return `
        <div class="bar ${m.key}${isCorrect ? " correct" : ""}" style="--o:var(${m.varName})">
          <svg class="bglyph" aria-hidden="true"><use href="#${m.shape}"/></svg>
          <div class="name">${esc(q.options[i] ?? "")}</div>
          <div class="track"><div class="fill" style="--w:${Math.round((count / max) * 100)}%"></div></div>
          <div class="end">${isCorrect ? `<span class="ctag"><svg class="ck"><use href="#s-ck"/></svg>Correct</span>` : ""}<span class="cnt">${count}</span></div>
        </div>`;
    }).join("");

    $("board").innerHTML = data.leaderboard.map((p, i) => `
      <div class="lrow${i === 0 ? " first" : ""}">
        <span class="rk">${i + 1}</span><span class="nm">${esc(p.nickname)}</span>
        <span class="pts">${p.score.toLocaleString()}</span>
      </div>`).join("");

    const isLast = q.index + 1 >= q.total;
    setNext(isLast ? "Final results 🏆" : "Next question ▸", true,
      isLast ? "That was the last question" : `Question ${q.index + 2} of ${q.total} is next`);
  });

  // ---- finished ----
  socket.on("game:finished", (data) => {
    stopTimer();
    show("finished");
    nextBtn.hidden = true;
    $("foot-hint").textContent = "Game over — download the CSV for grading/House points";

    const board = data.leaderboard;
    const podium = [board[1], board[0], board[2]]; // visual order: 2nd · 1st · 3rd
    const cls = ["p2", "p1", "p3"];
    const medal = ["2", "1", "3"];
    $("podium").innerHTML = podium.map((p, i) => p ? `
      <div class="pod ${cls[i]}">
        <div class="pnm">${esc(p.nickname)}</div>
        <div class="ppts">${p.score.toLocaleString()} pts</div>
        <div class="block">${medal[i]}</div>
      </div>` : "").join("");

    $("fin-rest").innerHTML = board.slice(3).map((p, i) => `
      <div class="lrow">
        <span class="rk">${i + 4}</span><span class="nm">${esc(p.nickname)}</span>
        <span class="pts">${p.score.toLocaleString()}</span>
      </div>`).join("");

    confetti();
  });

  // ---- celebration (skipped under prefers-reduced-motion) ----
  function confetti() {
    if (REDUCED_MOTION) return;
    const colors = ["#E35205", "#017BC4", "#E21B3C", "#D89E00", "#26890C"];
    const layer = document.createElement("div");
    layer.className = "confetti";
    layer.setAttribute("aria-hidden", "true");
    for (let i = 0; i < 70; i++) {
      const c = document.createElement("i");
      c.style.left = Math.random() * 100 + "vw";
      c.style.background = colors[i % colors.length];
      c.style.animationDuration = 2.4 + Math.random() * 2.2 + "s";
      c.style.animationDelay = Math.random() * 1.4 + "s";
      c.style.transform = `scale(${0.7 + Math.random() * 0.8})`;
      layer.appendChild(c);
    }
    document.body.appendChild(layer);
    setTimeout(() => layer.remove(), 6500);
  }
}

/* stride-drill.js — Week 1 simulation.
 *
 * WHAT THIS IS FOR
 * Six findings, one endpoint — the exact "STRIDE applied to /upload" slide,
 * turned into guess-first-then-reveal instead of a read-only bullet list.
 * The I (information disclosure) item is deliberately the hard one: the read
 * path is comparatively well-defended (Werkzeug's safe_join), so the naive
 * "I = read outside the folder" guess does NOT reproduce here — the real risk
 * on this endpoint is the write side (T). That correction is the point of
 * including it, not an edge case to smooth over.
 */
(function () {
  "use strict";

  var ITEMS = [
    {
      scenario: "There's no login on /upload at all — anyone can send a file as “anyone.”",
      answer: "S",
      explain: "Spoofing. Nothing verifies who's calling, so the endpoint can't tell you from an attacker."
    },
    {
      scenario: "A crafted filename makes the server write a file outside the uploads/ folder entirely.",
      answer: "T",
      explain: "Tampering. The filename is attacker-controlled and unsanitized on save — arbitrary-file-write, not just an overwrite of an existing file."
    },
    {
      scenario: "Nothing is logged, so nobody can prove which account uploaded a malicious file.",
      answer: "R",
      explain: "Repudiation. No log means no evidence — an attacker can deny it was them."
    },
    {
      scenario: "Trick one: on THIS endpoint pair specifically, is reading someone else's upload the live risk?",
      answer: "I",
      explain: "Information disclosure — and the honest answer is no, not much. The read path (/files/<name>) is the comparatively well-defended side (Werkzeug's safe_join blocks traversal there). This element's real risk sits on the write side, under T — don't let the STRIDE pass repeat the read-path mistake."
    },
    {
      scenario: "There's no size limit on the upload, so one request can fill the whole disk.",
      answer: "D",
      explain: "Denial of service. Unbounded input size is an easy way to take a service down."
    },
    {
      scenario: "Upload a file named shell.php, then just request it back — now it executes.",
      answer: "E",
      explain: "Elevation of privilege. Getting the server to run your code is the ceiling of what this bug can do."
    }
  ];

  var LETTERS = ["S", "T", "R", "I", "D", "E"];

  var idx = 0, score = 0, answered = false;

  var scenarioEl = document.getElementById("scenario");
  var explainEl = document.getElementById("explain");
  var qnEl = document.getElementById("qn");
  var scoreEl = document.getElementById("score");
  var answersEl = document.getElementById("answers");
  var nextBtn = document.getElementById("next");
  var doneEl = document.getElementById("done");

  function renderAnswers() {
    answersEl.innerHTML = "";
    LETTERS.forEach(function (letter) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "stride-drill-opt";
      b.textContent = letter;
      b.dataset.key = letter;
      b.addEventListener("click", onAnswer);
      answersEl.appendChild(b);
    });
  }

  function onAnswer(ev) {
    if (answered) return;
    answered = true;
    var chosen = ev.currentTarget.dataset.key;
    var item = ITEMS[idx];
    var correct = chosen === item.answer;
    if (correct) { score++; scoreEl.textContent = String(score); }

    var btns = answersEl.querySelectorAll(".stride-drill-opt");
    for (var i = 0; i < btns.length; i++) {
      var b = btns[i];
      b.disabled = true;
      if (b.dataset.key === item.answer) b.classList.add("is-correct");
      else if (b.dataset.key === chosen) b.classList.add("is-wrong");
      else b.classList.add("is-dim");
    }

    explainEl.textContent = (correct ? "✓ Right — " : "✗ Not quite — ") + item.explain;
    nextBtn.hidden = false;
    nextBtn.textContent = (idx === ITEMS.length - 1) ? "See results →" : "Next finding →";
  }

  function renderQuestion() {
    var item = ITEMS[idx];
    qnEl.textContent = String(idx + 1);
    scenarioEl.textContent = item.scenario;
    explainEl.textContent = "";
    answered = false;
    nextBtn.hidden = true;
    renderAnswers();
  }

  nextBtn.addEventListener("click", function () {
    idx++;
    if (idx >= ITEMS.length) {
      document.querySelector(".card").classList.add("quiz-finished");
      doneEl.classList.add("is-shown");
      return;
    }
    renderQuestion();
  });

  document.getElementById("total").textContent = String(ITEMS.length);
  document.getElementById("total2").textContent = String(ITEMS.length);
  renderQuestion();
})();

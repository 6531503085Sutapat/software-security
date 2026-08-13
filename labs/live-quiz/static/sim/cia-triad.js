/* cia-triad.js — Week 1 simulation.
 *
 * WHAT THIS IS FOR
 * The CIA triad is easy to recite and easy to misapply. Students learn it as
 * three words, then freeze the first time a real incident brushes more than
 * one of them (ransomware is availability AND usually confidentiality, since
 * the data was exfiltrated before it was encrypted). So this asks for the
 * PRIMARY hit on six real-shaped incidents, then explains the reasoning —
 * the reasoning is what the worksheet and exam actually grade, not the letter.
 *
 * Everything is static, local data. No network call, nothing sent anywhere.
 */
(function () {
  "use strict";

  var ITEMS = [
    {
      scenario: "Ransomware encrypts every file on a hospital's server — nobody can access patient records until it's paid.",
      answer: "A",
      explain: "Availability. The data may still exist, but the system isn't there when needed — that's the primary hit, even though modern ransomware usually bundles a confidentiality breach too (the data was likely stolen before it was encrypted)."
    },
    {
      scenario: "An attacker reads your medical records without permission. Nothing is changed or deleted.",
      answer: "C",
      explain: "Confidentiality. Only the right people should be able to read that data. Nothing here touches integrity or availability."
    },
    {
      scenario: "Someone secretly changes the price in your shopping cart from $50 to $5 before checkout.",
      answer: "I",
      explain: "Integrity. The data was tampered with, undetected — the price should only change when it's supposed to."
    },
    {
      scenario: "A DDoS attack floods the exam portal with traffic, taking it offline during finals week.",
      answer: "A",
      explain: "Availability. The system simply isn't there when the people who need it show up."
    },
    {
      scenario: "A leaked database exposes every student's username and password hash.",
      answer: "C",
      explain: "Confidentiality. Data that should have stayed private is now readable by people who shouldn't have it."
    },
    {
      scenario: "An attacker swaps in a modified version of a software update before it installs on your machine.",
      answer: "I",
      explain: "Integrity. The code was tampered with, undetected, between “published” and “installed.”"
    }
  ];

  var OPTIONS = [
    { key: "C", label: "Confidentiality" },
    { key: "I", label: "Integrity" },
    { key: "A", label: "Availability" }
  ];

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
    OPTIONS.forEach(function (opt) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "cia-triad-opt";
      b.textContent = opt.label;
      b.dataset.key = opt.key;
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

    var btns = answersEl.querySelectorAll(".cia-triad-opt");
    for (var i = 0; i < btns.length; i++) {
      var b = btns[i];
      b.disabled = true;
      if (b.dataset.key === item.answer) b.classList.add("is-correct");
      else if (b.dataset.key === chosen) b.classList.add("is-wrong");
      else b.classList.add("is-dim");
    }

    explainEl.textContent = (correct ? "✓ Right — " : "✗ Not quite — ") + item.explain;
    nextBtn.hidden = false;
    nextBtn.textContent = (idx === ITEMS.length - 1) ? "See results →" : "Next incident →";
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

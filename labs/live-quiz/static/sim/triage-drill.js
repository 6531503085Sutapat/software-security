/* triage-drill.js — Week 2 simulation.
 *
 * WHAT THIS IS FOR
 * Task 3 asks for a triage table, and the worksheet's own wording ("at least
 * 3 true positives and 1 likely false positive") is easy to read as "the
 * scan output will contain a false positive." It doesn't: running scan.sh
 * against vulnerable-repo for real returns 12 raw findings (10 Semgrep + 2
 * Gitleaks), and every one is a genuine true positive — confirmed by running
 * it, not assumed. The real triage skill this repo actually exercises is
 * DEDUPLICATION: 5 separate Semgrep rules fire on the identical 2-line SQLi,
 * and 3 fire on the identical 1-line command injection. Mistaking "5 rules
 * fired" for "5 bugs" is the realistic error, so that's what this drills —
 * map each raw finding to the ONE real bug underneath it, not TP-vs-FP.
 *
 * Every rule ID, file:line and code snippet below is copied from an actual
 * `bash scan.sh` run against this repo's own vulnerable-repo/app.py.
 */
(function () {
  "use strict";

  var BUGS = [
    { key: "sqli",   label: "SQL injection (/user)" },
    { key: "cmdi",   label: "Command injection (/ping)" },
    { key: "hash",   label: "Weak password hash" },
    { key: "debug",  label: "Debug mode left on" },
    { key: "secret", label: "Hardcoded credential" }
  ];

  var ITEMS = [
    {
      tool: "Semgrep", rule: "sql-injection-using-db-cursor-execute",
      loc: "app.py:19", snippet: "q = \"SELECT * FROM users WHERE name = '%s'\" % name",
      answer: "sqli",
      explain: "The first of five Semgrep rules that all fire on this same "
        + "two-line SQLi. Different rule, same root cause — this is card 1 of "
        + "that group."
    },
    {
      tool: "Semgrep", rule: "sqlalchemy-execute-raw-query",
      loc: "app.py:20", snippet: "return str(con.execute(q).fetchall())",
      answer: "sqli",
      explain: "Same bug as the sql-injection-using-db-cursor-execute card — a "
        + "different Semgrep rule matched the same line pair. In a real triage "
        + "table this is one row, not two: 5 rule hits, 1 fix."
    },
    {
      tool: "Semgrep", rule: "subprocess-shell-true",
      loc: "app.py:26", snippet: "subprocess.check_output(\"ping -c 1 \" + host, shell=True)",
      answer: "cmdi",
      explain: "shell=True with string-concatenated user input — classic OS "
        + "command injection. Fix idea: shell=False with an argument list, e.g. "
        + "[\"ping\", \"-c\", \"1\", host]."
    },
    {
      tool: "Semgrep", rule: "dangerous-subprocess-use",
      loc: "app.py:26", snippet: "subprocess.check_output(\"ping -c 1 \" + host, shell=True)",
      answer: "cmdi",
      explain: "Same line, same bug as the subprocess-shell-true card — the "
        + "second of three Semgrep rules that fire here. Three rule hits, one "
        + "root cause, one row in your triage table."
    },
    {
      tool: "Semgrep", rule: "insecure-hash-algorithm-md5",
      loc: "app.py:30", snippet: "hashlib.md5(pw.encode()).hexdigest()",
      answer: "hash",
      explain: "MD5 for password hashing, CWE-327. Fix idea: bcrypt or "
        + "argon2, not a faster general-purpose hash — the whole point of a "
        + "password hash is being slow to brute-force."
    },
    {
      tool: "Semgrep", rule: "debug-enabled",
      loc: "app.py:33", snippet: "app.run(debug=True)",
      answer: "debug",
      explain: "Flask's debugger exposes an interactive Python console on "
        + "any 500 error — CWE-489. Fix idea: debug=False, or read it from an "
        + "environment variable that defaults to off."
    },
    {
      tool: "Gitleaks", rule: "generic-api-key",
      loc: "app.py:11", snippet: "AWS_SECRET_ACCESS_KEY = \"hK8pQ2mN5vX9wZ3rT6yU1sA4bC7dE0fG2hJ5kL8\"",
      answer: "secret",
      explain: "A real-looking, high-entropy secret string hardcoded in "
        + "source — CWE-798. This is what makes it a genuine Gitleaks hit: a "
        + "placeholder like the AWS-docs example key would NOT have fired."
    }
  ];

  var idx = 0, score = 0, answered = false;

  var toolEl = document.getElementById("tool");
  var ruleEl = document.getElementById("rule");
  var locEl = document.getElementById("loc");
  var snippetEl = document.getElementById("snippet");
  var explainEl = document.getElementById("explain");
  var qnEl = document.getElementById("qn");
  var scoreEl = document.getElementById("score");
  var answersEl = document.getElementById("answers");
  var nextBtn = document.getElementById("next");
  var doneEl = document.getElementById("done");

  function renderAnswers() {
    answersEl.innerHTML = "";
    BUGS.forEach(function (bug) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "triage-drill-opt";
      b.textContent = bug.label;
      b.dataset.key = bug.key;
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

    var btns = answersEl.querySelectorAll(".triage-drill-opt");
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
    toolEl.textContent = item.tool;
    ruleEl.textContent = item.rule;
    locEl.textContent = item.loc;
    snippetEl.textContent = item.snippet;
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

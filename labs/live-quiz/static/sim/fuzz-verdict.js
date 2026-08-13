/* fuzz-verdict.js — Week 2 simulation.
 *
 * WHAT THIS IS FOR
 * The worksheet's Task 4 claims seeding matters and that unseeded runs "often
 * find nothing for minutes" — true, but unverifiable here and easy to
 * over-read as a precise statistic. What IS verifiable, and more useful to
 * see live, is the exact rule the harness checks: this re-implements
 * harness.c's LLVMFuzzerTestOneInput byte-for-byte, so typing "FUZ" against
 * "FUZZY" against "FUZ!" shows the real short-circuit boundary a fuzzer has
 * to land on — not an animation of one.
 *
 * No probability is claimed or simulated. Every verdict below is the literal
 * C logic run in JS on whatever bytes are typed.
 */
(function () {
  "use strict";

  var PRESETS = [
    { label: "hello", v: "hello" },
    { label: "FUZ", v: "FUZ" },
    { label: "FUZ!", v: "FUZ!" },
    { label: "FUZZ", v: "FUZZ" },
    { label: "FUZZY", v: "FUZZY" }
  ];

  // Mirrors harness.c's LLVMFuzzerTestOneInput exactly: each byte position is
  // only checked if every earlier check already passed, and data[3] is read
  // with no `size > 3` guard — the planted bug.
  function evaluate(bytes) {
    var steps = [null, null, null, null]; // pass | fail | unreached, per position 0-3
    var size = bytes.length;

    if (!(size > 0 && bytes[0] === "F".charCodeAt(0))) {
      steps[0] = size > 0 ? "fail" : "unreached";
      return { steps: steps, verdict: "safe" };
    }
    steps[0] = "pass";

    if (!(size > 1 && bytes[1] === "U".charCodeAt(0))) {
      steps[1] = size > 1 ? "fail" : "unreached";
      return { steps: steps, verdict: "safe" };
    }
    steps[1] = "pass";

    if (!(size > 2 && bytes[2] === "Z".charCodeAt(0))) {
      steps[2] = size > 2 ? "fail" : "unreached";
      return { steps: steps, verdict: "safe" };
    }
    steps[2] = "pass";

    // The planted bug: data[3] is read with no size>3 check. size===3 means
    // this read is one byte past the end of the buffer.
    if (size === 3) {
      steps[3] = "oob";
      return { steps: steps, verdict: "overflow" };
    }

    if (bytes[3] === "Z".charCodeAt(0)) {
      steps[3] = "pass";
      return { steps: steps, verdict: "trap" };
    }
    steps[3] = "fail";
    return { steps: steps, verdict: "safe" };
  }

  var input = document.getElementById("bytes");
  var presetsEl = document.getElementById("presets");
  var cellsEl = document.getElementById("cells");
  var verdictEl = document.getElementById("verdict");
  var explainEl = document.getElementById("explain");
  var sizeEl = document.getElementById("size");

  var LABELS = ["data[0]", "data[1]", "data[2]", "data[3]"];

  function byteChar(bytes, i) {
    if (i >= bytes.length) return "—"; // em dash: no byte here
    var c = String.fromCharCode(bytes[i]);
    return c === " " ? "␣" : c; // visible space glyph
  }

  function render(bytes, result) {
    sizeEl.textContent = String(bytes.length);
    cellsEl.innerHTML = "";
    for (var i = 0; i < 4; i++) {
      var cell = document.createElement("div");
      var state = result.steps[i] || "unreached";
      cell.className = "fuzz-verdict-cell is-" + state;
      var lbl = document.createElement("div");
      lbl.className = "fuzz-verdict-lbl";
      lbl.textContent = LABELS[i];
      var val = document.createElement("div");
      val.className = "fuzz-verdict-val";
      val.textContent = byteChar(bytes, i);
      cell.appendChild(lbl);
      cell.appendChild(val);
      cellsEl.appendChild(cell);
    }

    verdictEl.className = "verdict " + (result.verdict === "safe" ? "ok" : "bad");
    if (result.verdict === "safe") {
      verdictEl.textContent = "returns 0 — no crash";
      explainEl.textContent = "Every check up to the first mismatch (or the end of "
        + "the input) passed, then the chain broke — the function falls through "
        + "to `return 0` before reaching the unguarded read.";
    } else if (result.verdict === "overflow") {
      verdictEl.textContent = "heap-buffer-overflow — ASan crash";
      explainEl.textContent = "data[0..2] are exactly “FUZ” and the buffer is "
        + "exactly 3 bytes long. The next line reads data[3] with no `size > 3` "
        + "guard — that read is one byte past the allocation. This is the "
        + "planted bug in harness.c:23, and it needs no 4th byte at all.";
    } else {
      verdictEl.textContent = "__builtin_trap() — deliberate abort";
      explainEl.textContent = "The buffer is 4+ bytes, so reading data[3] is in "
        + "bounds — no memory-safety bug here. But its value is ‘Z’, so "
        + "the code's OWN check fires and it self-destructs on purpose. Different "
        + "failure class from the overflow above: this one a debugger sees as a "
        + "clean trap, not an ASan report.";
    }
  }

  function update() {
    var s = input.value;
    var bytes = [];
    for (var i = 0; i < s.length; i++) bytes.push(s.charCodeAt(i) & 0xff);
    render(bytes, evaluate(bytes));
  }

  PRESETS.forEach(function (p) {
    var b = document.createElement("button");
    b.type = "button";
    b.textContent = p.label;
    b.addEventListener("click", function () { input.value = p.v; update(); input.focus(); });
    presetsEl.appendChild(b);
  });
  input.addEventListener("input", update);
  update();
})();

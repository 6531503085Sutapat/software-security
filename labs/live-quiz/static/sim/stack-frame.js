/* stack-frame.js — Week 11 simulation.
 *
 * WHAT THIS IS FOR
 * Students can recite "the canary stops the overflow". It does not. It detects
 * a frame that has ALREADY been smashed, in the epilogue, after every byte was
 * written. And on this lab's own `make vuln-hardened` binary the canary never
 * even gets to speak: FORTIFY_SOURCE's __strcpy_chk aborts at copy time, so the
 * message students actually see is "buffer overflow detected", not "stack
 * smashing detected". That mix-up is the week's most reliable wrong answer.
 *
 * So the diagram is not the point — the ORDER is. Every state shows three
 * steps (copy -> epilogue canary check -> ret) and marks which one aborted.
 *
 * COUNTING. The slider counts BYTES WRITTEN INTO buf, including the NUL that
 * strcpy always appends. That is not a cosmetic choice: glibc's __strcpy_chk
 * does `if (strlen(src) >= destlen) __chk_fail()`, i.e. it aborts exactly when
 * more than 64 bytes would be written. Counting string LENGTH instead would
 * make "64 bytes fits" a lie — a 64-character string needs 65 bytes and already
 * spills one past the end.
 *
 * FRAME LAYOUT. With no canary: buf 0-63, saved RBP 64-71, return address
 * 72-79 — which is exactly `OFFSET = 72` in the lab's exploit_skeleton.py, and
 * an 80-byte payload. Compiling the canary in MOVES the return address to
 * 80-87. The offset moving is itself the lesson ("do not trust 72 blindly"), so
 * no phantom canary row is drawn when the canary is off.
 *
 * Everything is computed here. No network, no storage — the page is framed with
 * allow-scripts and WITHOUT allow-same-origin, so its origin is opaque and even
 * touching localStorage would throw.
 */
(function () {
  "use strict";

  var TOTAL = 96;   /* bytes drawn: the frame plus a little of the caller's */
  var BUF = 64;     /* sizeof buf */
  var WORD = 8;     /* x86-64 word: one grid row */

  var PRESETS = [
    { label: "64 B — fits exactly", flags: "make vuln · -fno-stack-protector",
      n: 64, canary: false, fortify: false },
    { label: "72 B — saved RBP gone", flags: "make vuln · -fno-stack-protector",
      n: 72, canary: false, fortify: false },
    { label: "80 B — attacker controls RIP", flags: "make vuln · the lab's ret2win payload",
      n: 80, canary: false, fortify: false },
    /* 72 with the canary in exists to make ONE point: the frame dies with the
       return address still untouched. Without it the only canary preset is 88,
       where RIP is overwritten too, and a student can walk away thinking the
       canary is what stopped the ret2win — rather than that the check never
       asked how far the overflow went. */
    { label: "72 B, canary on — RIP untouched, still dead", flags: "-fstack-protector-strong",
      n: 72, canary: true, fortify: false },
    { label: "88 B, canary on — detected", flags: "-fstack-protector-strong",
      n: 88, canary: true, fortify: false },
    { label: "make vuln-hardened — FORTIFY aborts",
      flags: "-fstack-protector-strong -D_FORTIFY_SOURCE=2 -O2 · (+ PIE/ASLR + NX, not modelled here)",
      n: 88, canary: true, fortify: true }
  ];

  var BADGE = {
    ok: "OK",
    pwn: "EXECUTES ANYWAY",
    abort: "ABORT",
    dead: "NEVER REACHED",
    skip: "NOT COMPILED IN"
  };

  var range = document.getElementById("n");
  var nbox = document.getElementById("nbox");
  var cbCanary = document.getElementById("canary");
  var cbFortify = document.getElementById("fortify");
  var grid = document.getElementById("grid");
  var statusEl = document.getElementById("status");
  var whyEl = document.getElementById("why");
  var stepsEl = document.getElementById("steps");
  var presetBar = document.getElementById("presets");

  var presetButtons = [];

  /* ---------------------------------------------------------------- layout */

  /* The rows of the frame, low address first. Eight bytes per row, so every
     row is exactly one region and no row ever straddles two. */
  function layout(canaryOn) {
    var rows = [];
    var at = 0;
    while (at < BUF) { rows.push({ kind: "buf", name: "char buf[64]", from: at }); at += WORD; }
    if (canaryOn) { rows.push({ kind: "canary", name: "stack canary", from: at }); at += WORD; }
    rows.push({ kind: "rbp", name: "saved RBP", from: at }); at += WORD;
    rows.push({ kind: "ret", name: "saved return address", from: at }); at += WORD;
    while (at < TOTAL) { rows.push({ kind: "caller", name: "caller's frame", from: at }); at += WORD; }
    rows.forEach(function (r) { r.to = r.from + WORD - 1; });
    return rows;
  }

  function regionOf(rows, kind) {
    for (var i = 0; i < rows.length; i++) if (rows[i].kind === kind) return rows[i];
    return null;
  }

  /* ---------------------------------------------------------------- verdict */

  function analyse(n, canaryOn, fortifyOn) {
    var rows = layout(canaryOn);
    var rbp = regionOf(rows, "rbp");
    var ret = regionOf(rows, "ret");
    var out = { tone: "bad", status: "", why: [], steps: [], aborted: false };

    var tCopy = "strcpy(buf, src) — write " + n + " byte" + (n === 1 ? "" : "s") + " into buf[64]";
    var tCanary = "function epilogue — compare the stack canary";
    var tRet = "ret — pop bytes " + ret.from + "–" + ret.to + " into RIP";

    /* FORTIFY fires first, at copy time, whatever else is compiled in. */
    if (fortifyOn && n > BUF) {
      out.aborted = true;
      out.status = "*** buffer overflow detected ***: terminated";
      out.why.push("-O2 lets the compiler see that the destination is 64 bytes, so "
        + "strcpy becomes __strcpy_chk(buf, src, 64). It measures the source first "
        + "and aborts when the copy would not fit — before writing a single byte.");
      out.why.push("Look at the frame: nothing changed. FORTIFY is the only mitigation "
        + "here that PREVENTS the write. It is also what make vuln-hardened actually "
        + "trips on, so the message you get is this one, not the canary's.");
      out.steps = [
        { t: tCopy, s: "abort", note: "__strcpy_chk compares LENGTHS: strlen(src) = " + (n - 1)
            + " against 64 bytes of room, and it fails when that length reaches 64. "
            + (n - 1) + " >= 64, so it calls __chk_fail() instead of copying."
            /* Only true at exactly BUF+1 — past that the characters themselves
               overflow, not just the terminator. */
            + (n === BUF + 1
                ? " Note how narrow the margin is: all 64 characters would fit. It is the "
                  + "NUL after them that has nowhere to go, and that is enough to abort."
                : "") },
        { t: tCanary, s: canaryOn ? "dead" : "skip",
          note: canaryOn ? "The process is already dead. The canary never gets to speak — this is the swap students get wrong."
                         : "Not compiled in (-fno-stack-protector)." },
        { t: tRet, s: "dead", note: "Never reached." }
      ];
      return out;
    }

    /* No overflow at all. */
    if (n <= BUF) {
      out.tone = "ok";
      out.status = n + (n === 1 ? " byte fits" : " bytes fit")
        + " inside buf[64] — nothing outside the buffer is touched.";
      out.why.push("The count includes the NUL terminator, so 64 bytes means a "
        + "63-character string. A 64-character string needs 65 bytes and already "
        + "spills one byte past the end — that one byte is the whole bug class.");

      var fitNote = n === 0 ? "Nothing to copy."
        : n === 1 ? "The single byte lands in buf[0]."
        : "All " + n + " bytes land in buf[0]–buf[" + (n - 1) + "].";
      /* A toggle that changes NOTHING teaches that the toggle is decoration.
         FORTIFY is running here too — it is just passing, and a check that
         passes is invisible from the outside unless we say so. */
      if (fortifyOn) {
        /* Phrased in the CHECK's own units — strlen(src) against destlen — not
           in bytes-written. "64 needed, 64 available" would teach the boundary
           as needed == available, when __strcpy_chk fails at strlen >= 64, one
           byte lower in its own terms. Compare this note with the abort note
           below at n = 65: same two numbers, opposite outcome. */
        fitNote = "__strcpy_chk(buf, src, 64) runs first and compares LENGTHS, not "
          + "bytes written: strlen(src) = " + Math.max(0, n - 1) + " against 64 bytes "
          + "of room, and it fails only when that length reaches 64. "
          + Math.max(0, n - 1) + " < 64, so it hands off to the real copy. " + fitNote;
        out.why.push("FORTIFY is compiled in and it did run — it checked the length "
          + "and allowed the copy. A check that passes looks exactly like no check "
          + "at all from the outside, which is why you cannot tell a hardened binary "
          + "from a vulnerable one by watching it work. Push the slider one byte past "
          + "64 and it will speak.");
      }
      out.steps = [
        { t: tCopy, s: "ok", note: fitNote },
        { t: tCanary, s: canaryOn ? "ok" : "skip",
          note: canaryOn ? "The canary is untouched, so the comparison matches and the function returns normally."
                         : "Not compiled in (-fno-stack-protector)." },
        { t: tRet, s: "ok", note: "The saved return address is intact; execution returns to main()." }
      ];
      return out;
    }

    /* Overflow, canary compiled in. */
    if (canaryOn) {
      var canary = regionOf(rows, "canary");
      out.status = "*** stack smashing detected ***: terminated";
      out.why.push("Bytes " + canary.from + "–" + canary.to + " hold the canary and they "
        + "are already overwritten — the write happened. A canary DETECTS a smashed "
        + "frame. It does not prevent one.");
      if (n > ret.to) {
        out.why.push("The return address (" + ret.from + "–" + ret.to + ") is fully "
          + "overwritten too, so RIP would be attacker-controlled. The epilogue "
          + "compares the canary first and calls __stack_chk_fail, so the process "
          + "dies before ret ever reads that word.");
      } else if (n > ret.from) {
        out.why.push("The return address (" + ret.from + "–" + ret.to + ") is partly "
          + "overwritten, and never gets used.");
      } else {
        out.why.push("The return address (" + ret.from + "–" + ret.to + ") was not even "
          + "reached, and the process still dies. The check does not ask how far the "
          + "overflow went.");
      }
      out.why.push("Note the canary also moved the frame: with it compiled in, the return "
        + "address starts at byte " + ret.from + ", not 72.");
      /* The whole reason this simulation exists. Students reach for this message
         when asked what `make vuln-hardened` prints, and that build never gets
         far enough to print it. */
      if (!fortifyOn) {
        out.why.push("This is the message most people expect from make vuln-hardened — "
          + "and for this lab's binary it is the wrong one. That build also compiles in "
          + "FORTIFY, which fires at copy time and gets here first. Tick FORTIFY and "
          + "watch the message change.");
      }
      out.steps = [
        { t: tCopy, s: "ok", note: "Every one of the " + n + " bytes is written, including over the canary. Nothing stops the copy." },
        { t: tCanary, s: "abort", note: "The stored value no longer matches the reference; __stack_chk_fail() kills the process." },
        { t: tRet, s: "dead", note: "Never reached — the exploit fails here, not because the write failed." }
      ];
      return out;
    }

    /* Overflow, nothing compiled in: the teaching build. */
    var retState = "pwn";
    var retNote;
    if (n <= rbp.to + 1) {
      out.status = n + " bytes: the saved RBP is corrupted — the return address is still intact.";
      out.why.push("Bytes " + rbp.from + "–" + (n - 1) + " of the saved frame pointer are "
        + "gone. ret still returns to the real caller, but leave restores a garbage "
        + "RBP, so the caller addresses its locals from a bogus frame — a delayed, "
        + "confusing crash rather than a clean one.");
      retNote = "Returns to the real caller — with a broken frame pointer.";
      retState = "ok";
    } else if (n <= ret.to) {
      out.status = n + " bytes: the return address is PARTLY overwritten — "
        + (n - ret.from) + " of its 8 bytes.";
      out.why.push("RIP becomes a mix of attacker bytes and the original address, which "
        + "is almost never a valid address: SIGSEGV. Partial control is still just a "
        + "crash, which is why the payload pads to exactly " + ret.from + " bytes and "
        + "only then writes a whole address.");
      retNote = "Jumps to a half-corrupted address → SIGSEGV.";
    } else {
      out.status = n + " bytes: the return address is fully overwritten — the attacker controls RIP.";
      out.why.push(ret.from + " bytes of padding (64 for buf plus 8 for the saved RBP) put "
        + "the next 8 bytes exactly on the saved return address. That is "
        + "exploit_skeleton.py's OFFSET = " + ret.from + ", and the SMALLEST payload that "
        + "reaches RIP is " + (ret.from + WORD) + " bytes."
        + (n > ret.from + WORD
            ? " You are writing " + n + ", so " + (n - ret.from - WORD) + " byte"
              + (n - ret.from - WORD === 1 ? "" : "s") + " run on past it into the caller's "
              + "frame. They buy no extra control — RIP was already yours at "
              + (ret.from + WORD) + " — and in a real target the extra reach is what "
              + "corrupts something that crashes first."
            : ""));
      out.why.push("ret pops the attacker's word into RIP and the program jumps wherever "
        + "they chose — win() in this lab.");
      retNote = "Pops the attacker's word into RIP → jumps to win().";
    }
    out.why.push("Nothing detected anything: this build has no canary and no FORTIFY.");
    out.steps = [
      { t: tCopy, s: "ok", note: "Nothing checks the length. All " + n + " bytes are written." },
      { t: tCanary, s: "skip", note: "Not compiled in (-fno-stack-protector)." },
      { t: tRet, s: retState, note: retNote }
    ];
    return out;
  }

  /* ----------------------------------------------------------------- render */

  function cell(offset, n, aborted) {
    var d = document.createElement("span");
    var cls = "stack-frame-cell";
    var written = !aborted && offset < n;
    if (aborted) {
      cls += " stack-frame-cell--void";
      d.textContent = "·";
    } else if (!written) {
      d.textContent = "·";
    } else {
      cls += offset < BUF ? " stack-frame-cell--in" : " stack-frame-cell--smash";
      if (offset === n - 1) { cls += " stack-frame-cell--nul"; d.textContent = "0"; }
      else { d.textContent = "A"; }
    }
    d.className = cls;
    return d;
  }

  function renderGrid(n, canaryOn, aborted) {
    var rows = layout(canaryOn);
    grid.textContent = "";
    for (var i = rows.length - 1; i >= 0; i--) {
      var r = rows[i];
      var hit = 0, k;
      for (k = r.from; k <= r.to; k++) if (!aborted && k < n) hit++;

      var rowEl = document.createElement("div");
      rowEl.className = "stack-frame-row"
        + (r.kind === "buf" ? " stack-frame-row--buf" : "")
        + (hit > 0 && r.kind !== "buf" ? " stack-frame-row--hit" : "");

      var head = document.createElement("div");
      head.className = "stack-frame-rowhead";
      var name = document.createElement("span");
      name.className = "stack-frame-rowname";
      name.textContent = r.name;
      head.appendChild(name);

      var meta = document.createElement("span");
      meta.className = "stack-frame-rowmeta";
      var verdict;
      if (aborted) verdict = "— never written";
      else if (r.kind === "buf") verdict = hit > 0 ? "✓ in bounds" : "· untouched";
      else verdict = hit > 0 ? "✗ OVERWRITTEN" : "✓ intact";
      meta.textContent = "bytes " + r.from + "–" + r.to + " · " + verdict;
      head.appendChild(meta);

      if (r.from === 0) {
        var note = document.createElement("span");
        note.className = "stack-frame-rownote";
        note.textContent = "strcpy starts here and writes upward";
        head.appendChild(note);
      }
      rowEl.appendChild(head);

      var cells = document.createElement("div");
      cells.className = "stack-frame-cells";
      cells.setAttribute("aria-hidden", "true");
      for (k = r.from; k <= r.to; k++) cells.appendChild(cell(k, n, aborted));
      rowEl.appendChild(cells);

      grid.appendChild(rowEl);
    }
  }

  function renderVerdict(v) {
    statusEl.className = "verdict stack-frame-status " + (v.tone === "ok" ? "ok" : "bad");
    statusEl.textContent = v.status;

    whyEl.textContent = "";
    v.why.forEach(function (t) {
      var p = document.createElement("p");
      p.className = "stack-frame-why";
      p.textContent = t;
      whyEl.appendChild(p);
    });

    stepsEl.textContent = "";
    v.steps.forEach(function (s) {
      var li = document.createElement("li");
      li.className = "stack-frame-step stack-frame-step--" + s.s;
      var b = document.createElement("span");
      b.className = "stack-frame-badge stack-frame-badge--" + s.s;
      b.textContent = BADGE[s.s];
      li.appendChild(b);
      var t = document.createElement("span");
      t.className = "stack-frame-steptitle";
      t.textContent = s.t;
      li.appendChild(t);
      var nn = document.createElement("span");
      nn.className = "stack-frame-stepnote";
      nn.textContent = s.note;
      li.appendChild(nn);
      stepsEl.appendChild(li);
    });
  }

  function clamp(x) {
    if (isNaN(x)) return 0;
    return Math.max(0, Math.min(TOTAL, Math.round(x)));
  }

  function update(n) {
    var canaryOn = cbCanary.checked;
    var fortifyOn = cbFortify.checked;
    if (range.value !== String(n)) range.value = String(n);
    if (nbox.value !== String(n)) nbox.value = String(n);

    var v = analyse(n, canaryOn, fortifyOn);
    renderGrid(n, canaryOn, v.aborted);
    renderVerdict(v);

    presetButtons.forEach(function (rec) {
      var on = rec.p.n === n && rec.p.canary === canaryOn && rec.p.fortify === fortifyOn;
      rec.b.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  function current() { return clamp(parseInt(range.value, 10)); }

  PRESETS.forEach(function (p) {
    var b = document.createElement("button");
    b.type = "button";
    b.setAttribute("aria-pressed", "false");
    var l1 = document.createElement("span");
    l1.className = "stack-frame-pname";
    l1.textContent = p.label;
    b.appendChild(l1);
    var l2 = document.createElement("span");
    l2.className = "stack-frame-pflags";
    l2.textContent = p.flags;
    b.appendChild(l2);
    b.addEventListener("click", function () {
      cbCanary.checked = p.canary;
      cbFortify.checked = p.fortify;
      update(p.n);
    });
    presetBar.appendChild(b);
    presetButtons.push({ b: b, p: p });
  });

  range.addEventListener("input", function () { update(current()); });
  nbox.addEventListener("input", function () {
    var raw = nbox.value;
    if (raw === "" || raw === "-") return;      /* mid-typing: don't fight the user */
    update(clamp(parseInt(raw, 10)));
  });
  nbox.addEventListener("blur", function () { update(clamp(parseInt(nbox.value, 10))); });
  cbCanary.addEventListener("change", function () { update(current()); });
  cbFortify.addEventListener("change", function () { update(current()); });

  update(80);
})();

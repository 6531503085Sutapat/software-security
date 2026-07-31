/* ecdsa-malleability.js — Week 11 simulation (security-cryptography).
 *
 * WHAT THIS IS FOR
 * The lab's bank identifies a transaction by `sha256(str(r) + str(s))`. Students
 * run `exploit.py`, watch `total_withdrawn` go 100 then 200, and collect the
 * flag — often without ever seeing the one line that makes it work: `s` and
 * `n - s` are two spellings of the SAME authorization, and the txid is computed
 * over the spelling.
 *
 * So this page puts the two forms side by side, computes `n - s` with real
 * BigInt arithmetic against the real secp256k1 order, hashes both preimages with
 * a real SHA-256, and then lets the student post each form to two modelled banks
 * at once — the vulnerable one and the low-S one — and read WHY each request got
 * the status code it got.
 *
 * WHAT IS REAL AND WHAT IS MODELLED (stated on the page too, not just here)
 *   real: n, n - s, the low-S test s <= n//2, and every txid — the digests here
 *         match `hashlib.sha256((str(r)+str(s)).encode()).hexdigest()` exactly,
 *         which is the same expression as vulnerable_app.py's `txid_of`.
 *   real: the two "sample" presets are genuine secp256k1 signatures over
 *         b"withdraw 100 to attacker"; both (r,s) and (r,n-s) were verified with
 *         python-ecdsa before being pasted in here.
 *   modelled: the bank. There is NO elliptic-curve verification in this file —
 *         the status codes, the dedup set and the running total reproduce
 *         vulnerable_app.py / fixed_app.py's control flow, which is where the
 *         lesson is. The three contrived presets are arithmetic demonstrations
 *         and the page says so rather than claiming they verify.
 *
 * WHY A CONTRIVED s IS REJECTED BY BOTH MODELLED BANKS
 * An earlier draft let ANY s walk through to 200/200/flag. That was a lie with a
 * banner on it: both real apps call `VK.verify(...)` against a key generated at
 * container startup, so a made-up s answers 403 {"error": "bad signature"} —
 * `total_withdrawn` never moves and no flag is released. Worse, it taught the
 * exact misconception the lab exists to kill: that you can INVENT a signature.
 * Malleability reshapes a signature you already hold. So `isGenuine()` below
 * gates the modelled verify step, and it sits precisely where `VK.verify` sits
 * in the real handlers — AFTER the fixed bank's low-S check, so a high-S twin
 * still answers "non-canonical", never "bad signature", exactly as fixed_app.py
 * orders it.
 *
 * No network, no storage: the page is framed with `sandbox="allow-scripts"` and
 * WITHOUT `allow-same-origin`, so its origin is opaque and `localStorage` would
 * throw. `crypto.subtle` is avoided for the same reason — plus it is async and
 * absent on a plain-http lab host. SHA-256 is implemented below.
 */
(function () {
  "use strict";

  /* ── the curve order, exactly as in the lab ─────────────────────────────── */
  var N = BigInt("0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141");
  var HALF_N = N / 2n;   // BigInt division truncates; n is positive, so this is n//2
  var AMOUNT = 100;
  var AUTHORIZED_TOTAL = 100;
  var MESSAGE = "withdraw 100 to attacker";

  /* ── SHA-256, so the txid here is byte-identical to the bank's ──────────── */
  var K256 = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1,
    0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
    0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
    0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
    0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
    0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2];

  function rotr(x, k) { return ((x >>> k) | (x << (32 - k))) >>> 0; }

  function hex8(x) {
    var h = (x >>> 0).toString(16);
    while (h.length < 8) h = "0" + h;
    return h;
  }

  /* ASCII only — every string we hash is decimal digits, which is all the
   * preimage `str(r) + str(s)` can ever contain. */
  function sha256Hex(str) {
    var bytes = [], i, j;
    for (i = 0; i < str.length; i++) bytes.push(str.charCodeAt(i) & 0xff);

    var bitLen = bytes.length * 8;
    bytes.push(0x80);
    while (bytes.length % 64 !== 56) bytes.push(0);
    var hi = Math.floor(bitLen / 4294967296), lo = bitLen >>> 0;
    bytes.push((hi >>> 24) & 255, (hi >>> 16) & 255, (hi >>> 8) & 255, hi & 255);
    bytes.push((lo >>> 24) & 255, (lo >>> 16) & 255, (lo >>> 8) & 255, lo & 255);

    var H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
             0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
    var w = new Array(64);

    for (i = 0; i < bytes.length; i += 64) {
      for (j = 0; j < 16; j++) {
        w[j] = ((bytes[i + 4 * j] << 24) | (bytes[i + 4 * j + 1] << 16) |
                (bytes[i + 4 * j + 2] << 8) | bytes[i + 4 * j + 3]) >>> 0;
      }
      for (j = 16; j < 64; j++) {
        var x = w[j - 15], y = w[j - 2];
        var s0 = (rotr(x, 7) ^ rotr(x, 18) ^ (x >>> 3)) >>> 0;
        var s1 = (rotr(y, 17) ^ rotr(y, 19) ^ (y >>> 10)) >>> 0;
        w[j] = (w[j - 16] + s0 + w[j - 7] + s1) >>> 0;
      }
      var a = H[0], b = H[1], c = H[2], d = H[3];
      var e = H[4], f = H[5], g = H[6], h = H[7];
      for (j = 0; j < 64; j++) {
        var S1 = (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) >>> 0;
        var ch = ((e & f) ^ (~e & g)) >>> 0;
        var t1 = (h + S1 + ch + K256[j] + w[j]) >>> 0;
        var S0 = (rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) >>> 0;
        var maj = ((a & b) ^ (a & c) ^ (b & c)) >>> 0;
        var t2 = (S0 + maj) >>> 0;
        h = g; g = f; f = e; e = (d + t1) >>> 0;
        d = c; c = b; b = a; a = (t1 + t2) >>> 0;
      }
      H[0] = (H[0] + a) >>> 0; H[1] = (H[1] + b) >>> 0;
      H[2] = (H[2] + c) >>> 0; H[3] = (H[3] + d) >>> 0;
      H[4] = (H[4] + e) >>> 0; H[5] = (H[5] + f) >>> 0;
      H[6] = (H[6] + g) >>> 0; H[7] = (H[7] + h) >>> 0;
    }
    var out = "";
    for (i = 0; i < 8; i++) out += hex8(H[i]);
    return out;
  }

  function txidOf(r, s) { return sha256Hex(r.toString() + s.toString()); }

  /* ── presets ────────────────────────────────────────────────────────────────
   * `real:true` means the pair is a genuine secp256k1 signature over
   * b"withdraw 100 to attacker" and BOTH (r,s) and (r,n-s) were checked to
   * verify. The contrived ones exist to put the low-S rule's edge on screen and
   * are labelled as contrived — the page never claims they verify. */
  var SAMPLE_R_LOW = "72870955378538229431535951015547563407141753236704974184533041003575593376922";
  var SAMPLE_S_LOW = "21638640808789616945463221842115931236984622257185218285145276092474438038975";
  var SAMPLE_R_HIGH = "14095136512684161097044961463628994619409814221458149754643122971450626332411";
  var SAMPLE_S_HIGH = "69512598668567986492470187019469108708360257079504348441672153779597082491041";

  var PRESETS = [
    {
      label: "sample /sign — low-S",
      r: SAMPLE_R_LOW, s: SAMPLE_S_LOW, real: true,
      note: "A real signature from one run of the lab's /sign. This s landed in "
          + "the lower half, so the fixed bank will accept it and reject the twin."
    },
    {
      label: "sample /sign — high-S",
      r: SAMPLE_R_HIGH, s: SAMPLE_S_HIGH, real: true,
      note: "Also real: vulnerable_app.py's /sign does not normalise, so about "
          + "half of all runs hand you the high-S form instead. Watch what the "
          + "fixed bank does with it."
    },
    {
      label: "edge: s = n div 2",
      r: SAMPLE_R_LOW, s: HALF_N.toString(), real: false,
      note: "Contrived: the largest s the low-S rule still accepts. Its twin is "
          + "larger by exactly 1 and is rejected. Read this one in the two cards "
          + "above — the banks below answer 403, because an invented s is not a "
          + "signature."
    },
    {
      label: "edge: s = n div 2 + 1",
      r: SAMPLE_R_LOW, s: (HALF_N + 1n).toString(), real: false,
      note: "Contrived: the smallest high-S value — one more than the preset "
          + "above, and the twin of it. Again the badges are the lesson; the "
          + "banks below answer 403."
    },
    {
      label: "extreme: s = 1",
      r: SAMPLE_R_LOW, s: "1", real: false,
      note: "Contrived: s = 1 is low-S, so its twin n - 1 is a 78-digit number. "
          + "Both are one flip apart all the same. And 403 at both banks — if "
          + "s = 1 could withdraw anything, you would not need malleability."
    }
  ];

  /* ── elements ───────────────────────────────────────────────────────────── */
  var $ = function (id) { return document.getElementById(id); };
  var presetBox = $("presets"), actionBox = $("actions");
  var rVal = $("rval"), sIn = $("sin"), sNote = $("snote");
  var sA = $("sa"), sB = $("sb"), badgeA = $("badgea"), badgeB = $("badgeb");
  var txA = $("txa"), txB = $("txb");
  var txVerdict = $("txverdict"), verifyClaim = $("verifyclaim");
  var nOut = $("nval"), halfOut = $("halfval");

  var banks = [
    {
      key: "v", lowS: false, totalEl: $("totalv"), logEl: $("logv"),
      seen: null, total: 0
    },
    {
      key: "f", lowS: true, totalEl: $("totalf"), logEl: $("logf"),
      seen: null, total: 0
    }
  ];

  /* ── state ──────────────────────────────────────────────────────────────── */
  var curR = BigInt(SAMPLE_R_LOW);
  var curReal = true;               // is the LOADED preset a captured signature?
  var curPresetS = BigInt(SAMPLE_S_LOW);  // the s the preset loaded, for both of the below
  var curNote = PRESETS[0].note;
  var edited = false;               // has the student typed a value that is not the preset's s?

  /* Would the lab's bank verify the pair currently on screen?
   *
   * True for a captured signature and — this is the whole lesson — for its twin,
   * because n - s is the same authorization under the same key. False for
   * anything else, including every contrived preset and every value the student
   * invents, because `VK.verify` is checking against a private key nobody on
   * this page has. Typing the twin back in by hand therefore stays genuine,
   * which also un-sticks the "you edited it" wording on undo. */
  function isGenuine(s) {
    return curReal && (s === curPresetS || s === N - curPresetS);
  }

  /* ── small DOM helpers (textContent only; nothing here builds markup) ───── */
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }
  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

  /* ── parsing s ──────────────────────────────────────────────────────────── */
  function parseS(text) {
    var t = (text || "").replace(/[\s_,]/g, "");
    if (t === "") return { ok: false, why: "empty" };
    var neg = false;
    if (t.charAt(0) === "-") { neg = true; t = t.slice(1); }
    var v;
    if (/^0[xX][0-9a-fA-F]+$/.test(t)) v = BigInt(t);
    else if (/^[0-9]+$/.test(t)) v = BigInt(t);
    else return { ok: false, why: "not an integer" };
    return { ok: true, v: neg ? -v : v };
  }

  function isLowS(s) { return s > 0n && s <= HALF_N; }

  /* ── rendering the two forms ────────────────────────────────────────────── */
  function setBadge(node, s) {
    if (s === null) {
      node.className = "ecdsamal-badge";
      node.textContent = "— no value";
      return;
    }
    if (s <= 0n || s >= N) {
      node.className = "ecdsamal-badge high";
      node.textContent = "■ OUT OF RANGE ✗  a signature needs 0 < s < n";
      return;
    }
    if (isLowS(s)) {
      node.className = "ecdsamal-badge low";
      node.textContent = "● LOW-S ✓  s ≤ n div 2";
    } else {
      node.className = "ecdsamal-badge high";
      node.textContent = "▲ HIGH-S ✗  s > n div 2";
    }
  }

  function commonPrefix(a, b) {
    var i = 0;
    while (i < a.length && i < b.length && a.charAt(i) === b.charAt(i)) i++;
    return i;
  }

  function currentForms() {
    var p = parseS(sIn.value);
    if (!p.ok) return { ok: false, why: p.why };
    return { ok: true, s: p.v, twin: N - p.v };
  }

  function update() {
    rVal.textContent = curR.toString();
    var f = currentForms();

    if (!f.ok) {
      /* parseS already worked out WHICH way it is unusable; say that rather than
       * printing "not an integer" over an empty box. */
      var reason = (f.why === "empty") ? "s is blank" : "s is not an integer";
      sA.textContent = "(" + reason + ")";
      sB.textContent = "(" + reason + ")";
      txA.textContent = "—";
      txB.textContent = "—";
      setBadge(badgeA, null);
      setBadge(badgeB, null);
      txVerdict.className = "verdict bad";
      txVerdict.textContent = reason + ", so there is no txid to compare. "
        + "The bank answers 400 to this — try it.";
      verifyClaim.textContent = "";
    } else {
      sA.textContent = f.s.toString();
      sB.textContent = f.twin.toString();
      setBadge(badgeA, f.s);
      setBadge(badgeB, f.twin);
      var ta = txidOf(curR, f.s), tb = txidOf(curR, f.twin);
      txA.textContent = ta;
      txB.textContent = tb;

      var same = commonPrefix(ta, tb);
      txVerdict.className = "verdict bad";
      txVerdict.textContent = "The two txids differ" + (same === 0
        ? " from the very first character."
        : " after " + same + " matching character(s).")
        + " The dedup set is keyed on this string, so it files them as two "
        + "unrelated transactions.";

      verifyClaim.textContent = isGenuine(f.s)
        ? "Both forms are valid signatures for this one message and this one "
          + "public key — checked with python-ecdsa when this preset was made. "
          + "Verification recovers a point and compares only its x-coordinate; "
          + "replacing s with n - s negates that point, which flips y and leaves "
          + "x untouched. So the bank cannot tell them apart by verifying."
        : "Heads up: this s is a contrived value, not a captured signature. The "
          + "arithmetic on screen is exact (n - s, the low-S test, both txids), "
          + "but nothing here claims this pair verifies — and because it does "
          + "not, both banks below answer 403 \"bad signature\", just as the lab's "
          + "apps do. Malleability reshapes a signature you already hold; it "
          + "cannot forge one. Load a sample preset for the pair that really "
          + "verifies.";
    }

    sNote.textContent = !edited ? curNote
      : (f.ok && isGenuine(f.s))
        ? "You typed this preset's twin by hand — and it is still the same "
          + "authorization, so the banks still verify it. That is malleability "
          + "in one keystroke: a different s, an unchanged message and key."
        : "You edited s by hand. n - s, the low-S test and both txids are still "
          + "computed exactly, but an invented s is not a signature: both banks "
          + "answer 403 \"bad signature\" below, because the real apps verify "
          + "against a key that is not yours.";
  }

  /* ── the two banks ──────────────────────────────────────────────────────────
   * Control flow copied from vulnerable_app.py / fixed_app.py's `withdraw`:
   *   400  sig_r/sig_s must be integers
   *   403  (fixed only, checked FIRST) non-canonical: s must be <= n/2
   *   403  bad signature   ← where VK.verify() sits, modelled by isGenuine()
   *   409  replay: txid already processed
   *   200  processed  →  total_withdrawn += 100
   * No curve arithmetic is performed; see the file header. The ORDER matters as
   * much as the codes: the low-S check has to stay above the verify step or the
   * fixed bank would answer "bad signature" to a high-S twin that fixed_app.py
   * answers "non-canonical" to. */
  function submit(bank, formName) {
    var f = currentForms();
    var entry = { form: formName };

    if (!f.ok) {
      entry.code = 400; entry.kind = "bad";
      entry.body = '{"error": "sig_r/sig_s must be integers"}';
      entry.why = "Flask does int(body[\"sig_s\"]) and it raises. The request "
        + "never reaches a signature check.";
      return log(bank, entry);
    }

    var s = (formName === "A") ? f.s : f.twin;

    if (bank.lowS && !isLowS(s)) {
      entry.code = 403; entry.kind = "bad";
      entry.body = '{"error": "non-canonical signature: s must be <= n/2 (BIP-62 low-S)"}';
      entry.why = "s is in the upper half, so is_low_s() fails before any "
        + "verification or dedup happens. Because n is odd, exactly one of "
        + "s and n - s is ≤ n div 2 — and this is the other one."
        /* `!edited` is load-bearing, not redundant with isGenuine(): the twin is
         * genuine too, so without it this sentence blames /sign for a high-S
         * value the student typed in themselves. It is only true of a preset
         * that arrived high-S and has not been touched. */
        + (formName === "A" && !edited && isGenuine(f.s)
            ? " Your captured s was already the high one, which is why the fixed "
              + "/sign normalises s down to n - s before handing it to you."
            : "");
      return log(bank, entry);
    }

    if (s <= 0n || s >= N || curR <= 0n || curR >= N) {
      entry.code = 403; entry.kind = "bad";
      entry.body = '{"error": "bad signature"}';
      entry.why = "s must satisfy 0 < s < n to be a signature scalar at all, so "
        + "verification cannot pass.";
      return log(bank, entry);
    }

    /* VK.verify() — the step this page models rather than computes. A pair is
     * accepted here exactly when the real bank would accept it: a signature it
     * issued, or that signature's twin. */
    if (!isGenuine(s)) {
      entry.code = 403; entry.kind = "bad";
      entry.body = '{"error": "bad signature"}';
      entry.why = "This is where the real app calls VK.verify(), against a "
        + "private key generated inside the container that nobody else holds — "
        + "and this s was invented, not captured, so it fails. Read that "
        + "carefully: malleability RESHAPES a signature you already have into a "
        + "second valid spelling. It does not let you forge one. Nothing is "
        + "withdrawn and no flag is released. Load a sample preset to run the "
        + "real double spend.";
      return log(bank, entry);
    }

    var t = txidOf(curR, s);
    entry.txid = t;
    if (bank.seen.has(t)) {
      entry.code = 409; entry.kind = "dup";
      entry.body = '{"error": "replay: txid already processed", "txid": "' + t + '"}';
      entry.why = "Same (r, s) → same preimage → same txid, already in "
        + "_seen_txids. The replay defence works exactly as designed; it simply "
        + "never sees the twin.";
      return log(bank, entry);
    }

    bank.seen.add(t);
    bank.total += AMOUNT;
    entry.code = 200;
    entry.kind = "ok";
    entry.total = bank.total;
    if (bank.total > AUTHORIZED_TOTAL) {
      entry.kind = "spend";
      entry.flag = true;
      entry.body = '{"status": "processed", "txid": "' + t + '", "amount": 100, '
        + '"total_withdrawn": ' + bank.total + ', "double_spend_detected": true, '
        + '"flag": "FLAG{…}"}';
      entry.why = "This txid had never been seen, so the bank processed it — but "
        + "it is the same authorization as the previous request, spelled with "
        + "n - s. total_withdrawn " + bank.total + " > AUTHORIZED_TOTAL 100.";
    } else {
      entry.body = '{"status": "processed", "txid": "' + t + '", "amount": 100, '
        + '"total_withdrawn": ' + bank.total + '}';
      entry.why = "New txid, so the bank processes it. total_withdrawn is now "
        + bank.total + " — exactly what the account owner authorized.";
    }
    return log(bank, entry);
  }

  function log(bank, entry) {
    if (bank.empty) { clear(bank.logEl); bank.empty = false; }

    var row = el("div", "ecdsamal-row " + entry.kind);
    var mark = entry.kind === "ok" || entry.kind === "spend" ? "✓"
             : entry.kind === "dup" ? "↻" : "✗";
    row.appendChild(el("p", "ecdsamal-head",
      mark + " " + entry.code + "  ·  POST /withdraw  ·  form "
      + entry.form + (entry.form === "A" ? " (r, s)" : " (r, n − s)")));
    row.appendChild(el("div", "q", entry.body));
    if (entry.flag) {
      row.appendChild(el("p", "ecdsamal-flag",
        "Flag released. (Redacted here — the real value is your instance's "
        + "FLAG_SIG environment variable.)"));
    }
    row.appendChild(el("p", "ecdsamal-why", "Why: " + entry.why));
    bank.logEl.appendChild(row);
    renderTotals();
  }

  function renderTotals() {
    banks.forEach(function (b) {
      var over = b.total > AUTHORIZED_TOTAL;
      b.totalEl.className = "ecdsamal-total" + (over ? " over" : "");
      b.totalEl.textContent = "total_withdrawn: " + b.total
        + (over ? "  ✗ over the 100 authorized" : "  of 100 authorized");
    });
  }

  function resetBanks() {
    banks.forEach(function (b) {
      b.seen = new Set();
      b.total = 0;
      b.empty = true;
      clear(b.logEl);
      b.logEl.appendChild(el("p", "ecdsamal-empty", "No requests yet."));
    });
    renderTotals();
  }

  function submitBoth(formName) {
    banks.forEach(function (b) { submit(b, formName); });
  }

  /* ── wiring ─────────────────────────────────────────────────────────────── */
  function loadPreset(p) {
    curR = BigInt(p.r);
    curReal = p.real;
    curPresetS = BigInt(p.s);
    curNote = p.note;
    edited = false;
    sIn.value = p.s;
    resetBanks();
    update();
  }

  PRESETS.forEach(function (p) {
    var b = el("button", "ecdsamal-btn", p.label);
    b.type = "button";
    b.addEventListener("click", function () { loadPreset(p); });
    presetBox.appendChild(b);
  });

  [
    { label: "POST form A  (r, s)", fn: function () { submitBoth("A"); } },
    { label: "POST form B  (r, n − s)", fn: function () { submitBoth("B"); } },
    {
      label: "Run the whole attack",
      fn: function () { resetBanks(); submitBoth("A"); submitBoth("B"); }
    },
    { label: "Reset both banks", fn: resetBanks }
  ].forEach(function (a) {
    var b = el("button", "ecdsamal-btn", a.label);
    b.type = "button";
    b.addEventListener("click", a.fn);
    actionBox.appendChild(b);
  });

  /* `edited` tracks the VALUE, not the act of typing: retyping the preset's own
   * s clears it again, so the page stops claiming a hand-edit that is no longer
   * there. Typing the twin leaves `edited` true — the student did change it —
   * but isGenuine() still holds, so the verification claim survives. */
  sIn.addEventListener("input", function () {
    var p = parseS(sIn.value);
    edited = !(p.ok && p.v === curPresetS);
    update();
  });

  nOut.textContent = N.toString();
  halfOut.textContent = HALF_N.toString();
  loadPreset(PRESETS[0]);
})();

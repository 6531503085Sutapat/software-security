/* jwt-forge.js — Week 6 simulation (authentication & authorisation).
 *
 * WHAT THIS IS FOR
 * Students meet JWTs as "the login token" and read the base64url as if it were
 * a seal. It is not. The browser holds all three parts and can retype any of
 * them. The only thing standing between a `role: user` token and a `role:
 * admin` one is a check the server may or may not perform — so this shows the
 * same token going through two verifiers side by side, and says in words why
 * each one decided what it decided.
 *
 * HONESTY
 * The signature here is a real HMAC-SHA256, computed with crypto.subtle where
 * WebCrypto exists and by the SHA-256 in this file where it does not (a lecture
 * laptop served over plain http on the room LAN is not a secure context, and
 * crypto.subtle is simply absent there). The fallback was checked against
 * Node's crypto for base64url round trips, SHA-256 across block boundaries, and
 * HMAC with keys shorter than, equal to and longer than the 64-byte block. The
 * UI says which one ran. Nothing is faked, and nothing is sent anywhere: there
 * is no server in this page, no fetch, no storage.
 *
 * The demo key below is a demo key. On a real service the whole security of the
 * scheme is that this value exists only on the server.
 */
(function () {
  "use strict";

  var B64U = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

  /* base64url, written out rather than borrowed from btoa/atob: students are
   * asked to state what the dots separate, and btoa would also throw on any
   * non-Latin-1 character in a name claim. */
  function bytesToB64u(bytes) {
    var out = "", i = 0, n;
    for (; i + 2 < bytes.length; i += 3) {
      n = (bytes[i] << 16) | (bytes[i + 1] << 8) | bytes[i + 2];
      out += B64U[(n >>> 18) & 63] + B64U[(n >>> 12) & 63]
           + B64U[(n >>> 6) & 63] + B64U[n & 63];
    }
    var rem = bytes.length - i;
    if (rem === 1) {
      n = bytes[i] << 16;
      out += B64U[(n >>> 18) & 63] + B64U[(n >>> 12) & 63];
    } else if (rem === 2) {
      n = (bytes[i] << 16) | (bytes[i + 1] << 8);
      out += B64U[(n >>> 18) & 63] + B64U[(n >>> 12) & 63] + B64U[(n >>> 6) & 63];
    }
    return out;
  }

  function b64uToBytes(s) {
    var clean = String(s).replace(/=+$/, "");
    var acc = 0, bits = 0, out = [], i, v;
    for (i = 0; i < clean.length; i++) {
      v = B64U.indexOf(clean.charAt(i));
      if (v < 0) return null;                 // not base64url — caller reports it
      acc = ((acc << 6) | v) & 0xFFFFFF;
      bits += 6;
      if (bits >= 8) { bits -= 8; out.push((acc >>> bits) & 255); }
    }
    return new Uint8Array(out);
  }

  function utf8Bytes(str) { return new TextEncoder().encode(str); }

  function b64uEncodeText(str) { return bytesToB64u(utf8Bytes(str)); }

  function b64uDecodeText(s) {
    var b = b64uToBytes(s);
    if (b === null) return null;
    try { return new TextDecoder("utf-8", { fatal: true }).decode(b); }
    catch (e) { return null; }
  }

  /* ---- SHA-256 / HMAC in plain JS -------------------------------------
   * Only used when crypto.subtle is missing, which happens whenever the
   * platform is served over plain http (a laptop on the room LAN at
   * http://<ip>:8080 is not a secure context). The UI says which one ran.
   */
  var SHA_K = [
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];

  function rotr(x, n) { return (x >>> n) | (x << (32 - n)); }

  function sha256Bytes(bytes) {
    var len = bytes.length;
    var total = ((len + 9 + 63) >> 6) << 6;
    var m = new Uint8Array(total);
    m.set(bytes);
    m[len] = 0x80;
    var hi = Math.floor(len / 536870912);      // high 32 bits of len*8
    var lo = (len * 8) >>> 0;
    m[total - 8] = (hi >>> 24) & 255; m[total - 7] = (hi >>> 16) & 255;
    m[total - 6] = (hi >>> 8) & 255;  m[total - 5] = hi & 255;
    m[total - 4] = (lo >>> 24) & 255; m[total - 3] = (lo >>> 16) & 255;
    m[total - 2] = (lo >>> 8) & 255;  m[total - 1] = lo & 255;

    var H = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
             0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    var w = new Array(64), i, t, a, b, c, d, e, f, g, h, s0, s1, ch, maj, t1, t2;

    for (t = 0; t < total; t += 64) {
      for (i = 0; i < 16; i++) {
        w[i] = (m[t + i * 4] << 24) | (m[t + i * 4 + 1] << 16)
             | (m[t + i * 4 + 2] << 8) | m[t + i * 4 + 3];
      }
      for (i = 16; i < 64; i++) {
        s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >>> 3);
        s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >>> 10);
        w[i] = (w[i - 16] + s0 + w[i - 7] + s1) | 0;
      }
      a = H[0]; b = H[1]; c = H[2]; d = H[3];
      e = H[4]; f = H[5]; g = H[6]; h = H[7];
      for (i = 0; i < 64; i++) {
        s1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
        ch = (e & f) ^ (~e & g);
        t1 = (h + s1 + ch + SHA_K[i] + w[i]) | 0;
        s0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
        maj = (a & b) ^ (a & c) ^ (b & c);
        t2 = (s0 + maj) | 0;
        h = g; g = f; f = e; e = (d + t1) | 0;
        d = c; c = b; b = a; a = (t1 + t2) | 0;
      }
      H[0] = (H[0] + a) | 0; H[1] = (H[1] + b) | 0;
      H[2] = (H[2] + c) | 0; H[3] = (H[3] + d) | 0;
      H[4] = (H[4] + e) | 0; H[5] = (H[5] + f) | 0;
      H[6] = (H[6] + g) | 0; H[7] = (H[7] + h) | 0;
    }
    var out = new Uint8Array(32);
    for (i = 0; i < 8; i++) {
      out[i * 4] = (H[i] >>> 24) & 255; out[i * 4 + 1] = (H[i] >>> 16) & 255;
      out[i * 4 + 2] = (H[i] >>> 8) & 255; out[i * 4 + 3] = H[i] & 255;
    }
    return out;
  }

  function hmacSha256Bytes(keyBytes, msgBytes) {
    var k = keyBytes.length > 64 ? sha256Bytes(keyBytes) : keyBytes;
    var ip = new Uint8Array(64 + msgBytes.length);
    var op = new Uint8Array(64 + 32), i;
    for (i = 0; i < 64; i++) {
      var kb = i < k.length ? k[i] : 0;
      ip[i] = kb ^ 0x36;
      op[i] = kb ^ 0x5c;
    }
    ip.set(msgBytes, 64);
    op.set(sha256Bytes(ip), 64);
    return sha256Bytes(op);
  }

  /* ---- which engine signs -------------------------------------------- */

  var SUBTLE = (typeof crypto !== "undefined" && crypto && crypto.subtle
                && typeof crypto.subtle.importKey === "function")
             ? crypto.subtle : null;
  var ENGINE = SUBTLE ? "webcrypto" : "js";

  function hmacB64u(keyStr, msgStr) {
    var kb = utf8Bytes(keyStr), mb = utf8Bytes(msgStr);
    if (SUBTLE) {
      return SUBTLE.importKey("raw", kb, { name: "HMAC", hash: "SHA-256" },
                              false, ["sign"])
        .then(function (k) { return SUBTLE.sign("HMAC", k, mb); })
        .then(function (buf) { return bytesToB64u(new Uint8Array(buf)); })
        .catch(function () {          // e.g. policy-blocked WebCrypto
          ENGINE = "js"; renderEngine();
          return bytesToB64u(hmacSha256Bytes(kb, mb));
        });
    }
    return Promise.resolve(bytesToB64u(hmacSha256Bytes(kb, mb)));
  }

  /* Byte-by-byte with no early exit on a MISMATCH. The length check up front is
   * not an oversight and not hidden: HMAC output length is public, and every
   * constant-time compare in the standard libraries starts the same way. What
   * must not leak is HOW MUCH of a wrong guess was right, and that is what the
   * unbroken loop protects. Not because a browser demo has a timing threat
   * model, but because the line students copy out of here is the line they will
   * write on the server. */
  function safeEqual(a, b) {
    if (a.length !== b.length) return false;
    var r = 0;
    for (var i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
    return r === 0;
  }

  /* ---- the scenario --------------------------------------------------- */

  var DEMO_KEY = "kosen-demo-kosen-demo-kosen-demo";  // pretend server-side value
  var GUESS = "secret";                               // what an attacker tries
  var PINNED = "HS256";                               // the allowlist, all of it
  var IAT = 1780000000;

  function H(alg) { return JSON.stringify({ alg: alg, typ: "JWT" }); }
  function P(sub, role) {
    return JSON.stringify({ sub: sub, name: "Somchai P.", role: role, iat: IAT });
  }

  /* Sign the LITERAL base64url strings, never a re-serialised object: the
   * signature covers bytes, so rebuilding the JSON for display could reorder a
   * key and invalidate a signature this page just produced. */
  function makeToken(headerJson, payloadJson, key) {
    var p0 = b64uEncodeText(headerJson), p1 = b64uEncodeText(payloadJson);
    if (key === null) return Promise.resolve(p0 + "." + p1 + ".");
    return hmacB64u(key, p0 + "." + p1).then(function (sig) {
      return p0 + "." + p1 + "." + sig;
    });
  }

  var PRESETS = [
    { label: "1 · Genuine (role: user)",
      note: "A token the server issued: alg HS256, role user, signature computed with the server key. Both verifiers accept it.",
      build: function () { return makeToken(H(PINNED), P("student01", "user"), DEMO_KEY); } },

    { label: "2 · Payload edited → admin",
      note: "role flipped to admin in part 2. Part 3 is still the signature of the OLD payload — nothing else was touched.",
      build: function () {
        var p0 = b64uEncodeText(H(PINNED));
        var pUser = b64uEncodeText(P("student01", "user"));
        var pAdmin = b64uEncodeText(P("student01", "admin"));
        return hmacB64u(DEMO_KEY, p0 + "." + pUser).then(function (sig) {
          return p0 + "." + pAdmin + "." + sig;
        });
      } },

    { label: "3 · alg = none",
      note: "The classic forgery: the header claims there is no algorithm, and the signature is simply deleted.",
      build: function () { return makeToken(H("none"), P("student01", "admin"), null); } },

    { label: "4 · alg = NoNe",
      note: "Same forgery, different spelling. This is the one that walks past a filter written to block the string \"none\".",
      build: function () { return makeToken(H("NoNe"), P("student01", "admin"), null); } },

    { label: "5 · Re-signed, guessed key",
      note: "The attacker computed a genuine HMAC — using the guess \"secret\" instead of the server key. "
          + "Verifier B refuses, but read why carefully: not because signing is hard, only because the guess was wrong. "
          + "Nothing stops an attacker guessing offline against a token they already hold, as fast as their hardware allows. "
          + "A short or dictionary secret falls, and then the forged token verifies for real.",
      build: function () { return makeToken(H(PINNED), P("student01", "admin"), GUESS); } }
  ];

  /* ---- DOM ------------------------------------------------------------ */

  var el = {};
  ["presets", "token", "strip", "alg", "role", "sub", "sign-real", "sign-guess",
   "drop-sig", "action-note", "raw1", "dec1", "raw2", "dec2", "raw3", "dec3",
   "naive-verdict", "naive-why", "steps", "strict-verdict", "summary", "engine"
  ].forEach(function (id) { el[id] = document.getElementById(id); });

  function txt(tag, cls, s) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (s !== undefined && s !== null) n.textContent = s;
    return n;
  }
  function clear(n) { while (n.firstChild) n.removeChild(n.firstChild); }
  function badge(kind, s) { return txt("span", "jwt-forge-badge jwt-forge-" + kind, s); }
  function short(s) { return s.length > 22 ? s.slice(0, 22) + "…" : s; }

  /* ---- parsing -------------------------------------------------------- */

  /* `present` is not the same question as `s === ""`, and conflating them taught
   * something false: a one-part string used to be told its (nonexistent) third
   * part was "exactly what the alg=none forgery sends". The forgery keeps all
   * three parts and empties the last one. A malformed string is not a forgery. */
  function decodePart(s, present) {
    if (!present) {
      return { text: null, obj: null,
               err: "There is no part here at all — the token does not have that many dot-separated pieces." };
    }
    if (s === "") return { text: null, obj: null, err: "The part is present, but it is empty." };
    var t = b64uDecodeText(s);
    if (t === null) {
      return { text: null, obj: null,
               err: "Not base64url — it holds characters outside A–Z a–z 0–9 - _ , or the bytes are not UTF-8." };
    }
    var o;
    try { o = JSON.parse(t); }
    catch (e) { return { text: t, obj: null, err: "It decodes, but the result is not JSON." }; }
    if (o === null || typeof o !== "object" || Array.isArray(o)) {
      return { text: t, obj: null, err: "It decodes to JSON, but not to an object." };
    }
    return { text: t, obj: o, err: null };
  }

  function parse(raw) {
    var tok = String(raw).trim();
    var parts = tok.split(".");
    var p0 = parts[0] || "";
    var p1 = parts.length > 1 ? parts[1] : "";
    var p2 = parts.length > 2 ? parts[2] : "";
    return {
      tok: tok, parts: parts, threeParts: parts.length === 3,
      p0: p0, p1: p1, p2: p2, has3: parts.length > 2,
      /* Splitting always yields a parts[0], so part 1 always exists — it may be
       * the empty string. Parts 2 and 3 genuinely may not be there. */
      header: decodePart(p0, true),
      payload: decodePart(p1, parts.length > 1),
      signingInput: p0 + "." + p1
    };
  }

  function claim(t, name) {
    return (t.payload.obj && typeof t.payload.obj[name] === "string")
      ? t.payload.obj[name] : null;
  }

  /* An empty string is a claim that is present and empty — a different thing
   * from a claim that is missing, and both need saying out loud. */
  function shownClaim(t, name) {
    var v = claim(t, name);
    if (v === null) return "(no " + name + " claim)";
    return v === "" ? "(" + name + " is empty)" : v;
  }

  /* ---- the three panes ------------------------------------------------- */

  function renderStrip(t) {
    clear(el.strip);
    if (t.tok === "") {
      el.strip.appendChild(txt("span", "hint", "(the token is empty — pick a preset)"));
      return;
    }
    var tint = ["jwt-forge-p1", "jwt-forge-p2", "jwt-forge-p3"];
    t.parts.forEach(function (p, i) {
      if (i) el.strip.appendChild(txt("span", "jwt-forge-dot", "."));
      var cls = i < 3 ? tint[i] : "jwt-forge-extra";
      el.strip.appendChild(txt("span", cls, p === "" ? "∅" : p));
    });
  }

  function pane(rawEl, decEl, raw, part, tint) {
    clear(rawEl); clear(decEl);
    rawEl.appendChild(txt("span", tint, raw === "" ? "∅ empty" : raw));
    if (part.obj) {
      decEl.appendChild(txt("span", null, JSON.stringify(part.obj, null, 2)));
      return;
    }
    decEl.appendChild(txt("span", "jwt-forge-alert", "Cannot decode. " + part.err));
    if (part.text !== null) {
      decEl.appendChild(document.createElement("br"));
      decEl.appendChild(txt("span", "hint", part.text));
    }
  }

  function renderSigPane(t) {
    clear(el.raw3); clear(el.dec3);
    el.raw3.appendChild(txt("span", "jwt-forge-p3",
      !t.has3 ? "— no third part —" : (t.p2 === "" ? "∅ empty" : t.p2)));
    var msg;
    if (!t.has3) {
      msg = "This string has " + t.parts.length + " dot-separated part"
          + (t.parts.length === 1 ? "" : "s") + ", so there is no signature slot to look at. "
          + "That is a malformed string, not a forgery: the alg=none forgery keeps all three "
          + "parts and leaves the third one empty, which is a token a library will happily parse.";
    } else if (t.p2 === "") {
      msg = "The slot is there and empty. An empty third part is exactly what the alg=none forgery sends.";
    } else {
      var b = b64uToBytes(t.p2);
      if (b === null) msg = "Not base64url, so it is not a value this service ever produced.";
      else if (b.length === 32) msg = "32 bytes — the right size for an HMAC-SHA256 output. Size proves nothing about who made it; only recomputing it does.";
      else msg = b.length + " bytes. HMAC-SHA256 always produces 32.";
    }
    el.dec3.textContent = msg + " A signature is not encryption: there is nothing readable inside it, and it hides nothing in parts 1 and 2.";
  }

  /* ---- verifier A: decode only ---------------------------------------- */

  function renderNaive(t) {
    clear(el["naive-verdict"]); clear(el["naive-why"]);
    var ok = !!t.payload.obj;

    if (!ok) {
      el["naive-verdict"].appendChild(badge("skip", "✗ THREW"));
      el["naive-verdict"].appendChild(txt("span", "jwt-forge-vtext", "could not read part 2"));
      el["naive-why"].appendChild(txt("p", "jwt-forge-why",
        "Part 2: " + t.payload.err + " That is a parse failure, not a security decision — "
        + "this code path has no security decision to make."));
      return false;
    }

    var role = shownClaim(t, "role");
    var sub = shownClaim(t, "sub");
    el["naive-verdict"].appendChild(badge("pass", "✓ ACCEPTED"));
    el["naive-verdict"].appendChild(txt("span", "jwt-forge-vtext",
      "signed in as " + sub + " · role " + role));
    el["naive-why"].appendChild(txt("p", "jwt-forge-why",
      "Part 3 was never read. No key, no HMAC, no comparison: decode() splits on the dots and "
      + "base64-decodes. Every claim above is whatever the client typed."));
    if (role === "admin") {
      el["naive-why"].appendChild(txt("p", "jwt-forge-alert",
        "→ Admin unlocked by a string the browser sent."));
    }
    return true;
  }

  /* ---- verifier B: pinned algorithm + real HMAC ----------------------- */

  var seq = 0;

  function structureWhy(t) {
    if (!t.threeParts) {
      return "A JWS has exactly three dot-separated parts; this string has " + t.parts.length + ".";
    }
    if (!t.header.obj) return "Part 1 (header): " + t.header.err;
    return "Part 2 (payload): " + t.payload.err;
  }

  function algWhy(alg) {
    var shown = alg === null ? "no alg field at all" : "\"" + alg + "\"";
    var s = "Header says " + shown + ". The allowlist is [\"HS256\"] and this is not on it, so it stops here.";
    if (alg !== null && alg.toLowerCase() === "none") {
      s += " \"none\" means “there is no signature” — a library that honours it verifies nothing and hands back the claims anyway.";
      if (alg !== "none") {
        s += " A filter that blocked the exact string \"none\" would have missed this spelling. An allowlist cannot be spelled around.";
      }
    } else if (alg !== null) {
      s += " Even a different HMAC size is the attacker choosing which check runs.";
    }
    return s;
  }

  function sigWhy(match, presented) {
    if (match) {
      return "Recomputed HMAC-SHA256 over the exact bytes of part 1 + \".\" + part 2 with the server key, and it matches. "
        + "The comparison walks every byte and never stops at the first difference, so how long it takes "
        + "does not tell an attacker how much of a wrong signature was correct.";
    }
    if (presented === "") {
      return "There is no signature to compare with. The value it would have to be is below — and producing it needs the key.";
    }
    var b = b64uToBytes(presented);
    if (b && b.length === 32) {
      return "A well-formed 256-bit HMAC — but of different bytes, or under a different key. "
        + "Changing one character of the payload changes what the signature must be, and recomputing it needs "
        + "the server key: the browser does not hold it and can only try to guess it.";
    }
    return "What was presented is not a 32-byte HMAC-SHA256 output at all.";
  }

  function renderSteps(steps) {
    clear(el.steps);
    steps.forEach(function (s) {
      var li = document.createElement("li");
      li.appendChild(badge(s.st, s.st === "pass" ? "✓ PASS"
                                 : s.st === "fail" ? "✗ FAIL" : "— SKIPPED"));
      var body = txt("div", null);
      body.appendChild(txt("div", "jwt-forge-steptitle", s.n + ". " + s.title));
      body.appendChild(txt("p", "jwt-forge-why", s.why));
      if (s.cmp) {
        var c = txt("div", "q jwt-forge-cmp");
        c.appendChild(txt("div", null, "expected   " + short(s.cmp.expected)));
        c.appendChild(txt("div", null, "presented  "
          + (s.cmp.presented === "" ? "∅ nothing" : short(s.cmp.presented))));
        body.appendChild(c);
      }
      li.appendChild(body);
      el.steps.appendChild(li);
    });
  }

  function paint(mine, steps, accepted, naiveOk, t) {
    if (mine !== seq) return;
    renderSteps(steps);

    clear(el["strict-verdict"]);
    if (accepted === null) {
      el["strict-verdict"].appendChild(badge("skip", "… CHECKING"));
    } else {
      el["strict-verdict"].appendChild(badge(accepted ? "pass" : "fail",
        accepted ? "✓ ACCEPTED" : "✗ REJECTED"));
      /* Short on purpose: the verdict line must stay ONE line at the 427px
       * column the 4:3 worksheet iframe gives it, or it wraps and pushes
       * itself below the fold that a lecturer never scrolls past. */
      el["strict-verdict"].appendChild(txt("span", "jwt-forge-vtext", accepted
        ? "genuinely issued by the server"
        : "dropped, no claim is read"));
    }

    if (accepted === null) { el.summary.textContent = "…"; return; }
    var role = claim(t, "role");
    if (naiveOk && accepted) {
      el.summary.textContent = "Both verifiers agree — which is exactly why Verifier A looks fine right up "
        + "until someone edits part 2. Try preset 2.";
    } else if (naiveOk && !accepted) {
      el.summary.textContent = "Forged. "
        + (role ? "Verifier A hands over role " + role + "; Verifier B refuses."
                : "Verifier A trusts these claims; Verifier B refuses them.")
        + " No exploit and no memory corruption — a client retyped a string.";
    } else if (!naiveOk && !accepted) {
      el.summary.textContent = "Neither verifier can decode this. That is a broken token, not a clever one — "
        + "load a preset to get back to a working example.";
    } else {
      el.summary.textContent = "—";
    }
  }

  function renderStrict(t, naiveOk) {
    var mine = ++seq;

    var s1 = !!(t.threeParts && t.header.obj && t.payload.obj);
    var step1 = { n: "1", st: s1 ? "pass" : "fail", title: "Structure",
      why: s1 ? "Three dot-separated parts, and parts 1 and 2 both decode to JSON objects."
              : structureWhy(t) };

    var alg = (s1 && typeof t.header.obj.alg === "string") ? t.header.obj.alg : null;
    var s2 = s1 && alg === PINNED;
    var step2 = { n: "2", st: !s1 ? "skip" : (s2 ? "pass" : "fail"),
      title: "Algorithm pinned",
      why: !s1 ? "Not evaluated — nothing decoded to look at."
         : s2 ? "Header says \"HS256\", the one algorithm this service issues. It is compared against our allowlist; the token does not get a vote."
              : algWhy(alg) };

    if (!s1 || !s2) {
      paint(mine, [step1, step2, { n: "3", st: "skip", title: "Signature",
        why: !s1 ? "Not evaluated — there is nothing well-formed to check."
                 : "Not evaluated: the algorithm was rejected first. That order is the whole lesson — a verifier that reads alg out of the token lets the attacker choose which check runs." }],
        false, naiveOk, t);
      return;
    }

    paint(mine, [step1, step2, { n: "3", st: "skip", title: "Signature",
      why: "Recomputing HMAC-SHA256…" }], null, naiveOk, t);

    hmacB64u(DEMO_KEY, t.signingInput).then(function (expected) {
      if (mine !== seq) return;
      var match = safeEqual(expected, t.p2);
      paint(mine, [step1, step2, {
        n: "3", st: match ? "pass" : "fail", title: "Signature",
        why: sigWhy(match, t.p2),
        cmp: match ? null : { expected: expected, presented: t.p2 }
      }], match, naiveOk, t);
    });
  }

  /* ---- controls -------------------------------------------------------- */

  var pseq = 0;

  /* Idempotent because #action-note is an aria-live region: rewriting it with
   * the same string on every keystroke would make a screen reader re-announce
   * the sentence per character. */
  function note(s) {
    if (el["action-note"].textContent !== s) el["action-note"].textContent = s;
  }

  var HAND_NOTE = "You are editing the token by hand. Whatever is in the box is "
    + "what both verifiers below read — nothing here re-signs it for you.";

  /* Every async signer captures `pseq` before it starts and drops its result if
   * the counter moved. Bumping it here is what makes that guard cover the case
   * that matters: an HMAC is in flight (crypto.subtle resolves a task later,
   * with room for a click or a keystroke in between) and the student changes the
   * token meanwhile. Without this the stale signer wins and silently reverts the
   * edit they just made — measured, not assumed: clicking "Re-sign with the
   * server key" and then flipping role to admin used to put role back to user. */
  function setToken(tok, msg) {
    pseq++;
    el.token.value = tok;
    if (msg) note(msg);
    update();
  }

  function setSelect(sel, v) {
    var i;
    if (v !== null) {
      for (i = 0; i < sel.options.length; i++) {
        if (sel.options[i].value === v) {
          if (sel.selectedIndex !== i) sel.selectedIndex = i;
          return;
        }
      }
    }
    sel.selectedIndex = -1;      // the token holds something we do not offer
  }

  function syncControls(t) {
    setSelect(el.alg, (t.header.obj && typeof t.header.obj.alg === "string")
      ? t.header.obj.alg : null);
    setSelect(el.role, claim(t, "role"));

    /* Mirror the token, including the absence of a claim — a stale "student01"
     * sitting in the box under a payload that has no sub is the field lying
     * about what the token says. Only touched when the payload actually parsed,
     * so a half-typed token does not wipe what the student was editing. */
    if (t.payload.obj) {
      var sub = claim(t, "sub");
      if (sub === null) sub = "";
      if (el.sub.value !== sub) el.sub.value = sub;
    }
  }

  function setField(which, name, value, msg) {
    var t = parse(el.token.value);
    var part = which === "header" ? t.header : t.payload;
    if (!part.obj) {
      note("Part " + (which === "header" ? "1" : "2") + " is not valid JSON right now, "
         + "so there is no field to set. Load a preset to start again.");
      return;
    }
    part.obj[name] = value;
    var enc = b64uEncodeText(JSON.stringify(part.obj));
    setToken(which === "header" ? enc + "." + t.p1 + "." + t.p2
                                : t.p0 + "." + enc + "." + t.p2, msg);
  }

  function resign(key, msg) {
    var t = parse(el.token.value);
    var mine = ++pseq;
    hmacB64u(key, t.signingInput).then(function (sig) {
      if (mine !== pseq) return;
      setToken(t.p0 + "." + t.p1 + "." + sig, msg);
    });
  }

  function renderEngine() {
    el.engine.textContent = (ENGINE === "webcrypto"
      ? "Signatures here are real: HMAC-SHA256 through crypto.subtle."
      : "WebCrypto is not available to this page — browsers only hand out crypto.subtle over https or on localhost — so the SHA-256 written into this simulation computes the HMAC instead. Still a real check: it was verified against a reference implementation, not stubbed out.")
      + " Demo key: " + DEMO_KEY + ". On a real service this value only ever exists on the server, and that is the entire reason the scheme works.";
  }

  /* ---- wiring ---------------------------------------------------------- */

  function update() {
    var t = parse(el.token.value);
    renderStrip(t);
    pane(el.raw1, el.dec1, t.p0, t.header, "jwt-forge-p1");
    pane(el.raw2, el.dec2, t.p1, t.payload, "jwt-forge-p2");
    renderSigPane(t);
    syncControls(t);
    renderStrict(t, renderNaive(t));
  }

  PRESETS.forEach(function (p) {
    var b = txt("button", null, p.label);
    b.type = "button";
    b.addEventListener("click", function () {
      var mine = ++pseq;
      Promise.resolve(p.build()).then(function (tok) {
        if (mine !== pseq) return;
        setToken(tok, p.note);
      });
    });
    el.presets.appendChild(b);
  });

  el.token.addEventListener("input", function () {
    pseq++;              // typing beats any signature still being computed
    /* The cue line has to stop describing a preset the moment the token stops
     * being that preset, or it is a caption on the wrong picture — and this one
     * is the page's only "why" for the state the student is looking at. */
    note(HAND_NOTE);
    update();
  });

  el.alg.addEventListener("change", function () {
    setField("header", "alg", el.alg.value,
      "alg set to \"" + el.alg.value + "\" in part 1. The signature was left exactly as it was — "
      + "removing it is a separate button.");
  });

  el.role.addEventListener("change", function () {
    setField("payload", "role", el.role.value,
      "role set to \"" + el.role.value + "\" in part 2. Part 2 changed, so the signature over part 2 no longer fits.");
  });

  el.sub.addEventListener("input", function () {
    setField("payload", "sub", el.sub.value, "sub rewritten in part 2 — impersonation is the same edit as escalation.");
  });

  el["sign-real"].addEventListener("click", function () {
    resign(DEMO_KEY, "Re-signed with the server key. This is the step an attacker cannot take: the key is not in the browser.");
  });

  el["sign-guess"].addEventListener("click", function () {
    resign(GUESS, "Re-signed with the guess \"secret\". A structurally perfect HMAC, computed with the wrong key — "
         + "Verifier B still refuses. The only thing that made the guess wrong is that the real key is long and random.");
  });

  el["drop-sig"].addEventListener("click", function () {
    var t = parse(el.token.value);
    setToken(t.p0 + "." + t.p1 + ".", "Part 3 deleted. This is the shape of the alg=none forgery.");
  });

  renderEngine();
  update();                                  // a coherent page before any async
  note(PRESETS[0].note);
  (function () {
    var mine = ++pseq;
    Promise.resolve(PRESETS[0].build()).then(function (tok) {
      if (mine !== pseq) return;
      setToken(tok, PRESETS[0].note);
    });
  })();
})();

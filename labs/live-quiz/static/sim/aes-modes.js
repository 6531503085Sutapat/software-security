/* aes-modes.js — Week 3 simulation (labs/week03-cryptography).
 *
 * WHAT THIS IS FOR
 * Students can recite "ECB is bad". What transfers is *why*: ECB encrypts each
 * block independently, so equal plaintext blocks give equal ciphertext blocks,
 * and any structure made of repeated blocks survives encryption. So panel 1
 * encrypts a picture, blockwise, and shows the picture again.
 *
 * Panel 2 is the part the lab actually runs. CBC removes the leak by XORing each
 * block with the previous ciphertext — and that same XOR hands the attacker a
 * precise editing tool. Flip a bit in C0 and the *next* plaintext block flips
 * exactly that bit. Confidentiality without integrity is not enough, and this is
 * the concrete demonstration of it.
 *
 * The block cipher is a toy: 6 rounds of (substitute, chain-mix, shuffle) over
 * 16 bytes, invertible by construction. It is NOT AES, the page says so on
 * screen, and its only job is to be a deterministic 16-byte permutation so the
 * *mode* is the visible variable. Everything runs locally; nothing is fetched
 * and nothing is stored.
 */
(function () {
  "use strict";

  /* ===== CORE START =====
   * Pure: no DOM, no globals beyond these. The scratchpad property test
   * evaluates exactly this slice of this file, so what is tested is what ships.
   */

  var W = 128, H = 96, BS = 16, ROUNDS = 6;
  var NB = (W * H) / BS;                       // 768 blocks
  var TOKEN = "sess=8f2c1;user=guest;admin=0;v1";   // 32 bytes = 2 blocks

  function lcg(seed) {
    var s = seed >>> 0;
    return function () {
      s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
      return s;
    };
  }

  /* S-box and byte shuffle are FIXED for the life of the page. Changing the key
   * must change only the round keys — if the S-box moved too we would have
   * swapped the algorithm, not the key, and "same key, same block, same
   * ciphertext" would stop being a statement about ECB. */
  var SBOX = (function () {
    var a = new Uint8Array(256), r = lcg(0x5EED1234), i, j, t;
    for (i = 0; i < 256; i++) a[i] = i;
    for (i = 255; i > 0; i--) { j = r() % (i + 1); t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  })();

  var INV_SBOX = (function () {
    var a = new Uint8Array(256), i;
    for (i = 0; i < 256; i++) a[SBOX[i]] = i;
    return a;
  })();

  var PERM = (function () {
    var a = [], r = lcg(0x00C0FFEE), i, j, t;
    for (i = 0; i < BS; i++) a[i] = i;
    for (i = BS - 1; i > 0; i--) { j = r() % (i + 1); t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  })();

  /* Diffusion, in BOTH directions. This matters more than it looks: the panel-2
   * claim "the tampered block is destroyed" is a claim about *decryption*, so
   * one changed ciphertext byte has to disturb the whole decrypted block.
   *
   * A forward XOR chain diffuses beautifully going forward and hardly at all
   * coming back — its inverse is a local difference, and an earlier version of
   * this file used a pair of chains and left only 7 of 16 bytes damaged. So the
   * second step is a parity fold: XOR every byte with the XOR of all 16. That is
   * its own inverse (the parity of the result is unchanged) and one changed byte
   * moves 15 of the other 16 either way. Real AES gets this from MixColumns. */
  function parity(b) {
    var p = 0, i;
    for (i = 0; i < BS; i++) p ^= b[i];
    for (i = 0; i < BS; i++) b[i] ^= p;
  }
  function mix(b) {
    var i;
    for (i = 1; i < BS; i++) b[i] ^= b[i - 1];
    parity(b);
  }
  function unmix(b) {
    var i;
    parity(b);
    for (i = BS - 1; i >= 1; i--) b[i] ^= b[i - 1];
  }

  function encBlock(src, off, rk) {
    var b = new Uint8Array(BS), t = new Uint8Array(BS), i, r;
    for (i = 0; i < BS; i++) b[i] = src[off + i];
    for (r = 0; r < ROUNDS; r++) {
      for (i = 0; i < BS; i++) b[i] = SBOX[b[i] ^ rk[r][i]];
      mix(b);
      for (i = 0; i < BS; i++) t[i] = b[PERM[i]];
      b.set(t);
    }
    for (i = 0; i < BS; i++) b[i] ^= rk[ROUNDS][i];
    return b;
  }

  function decBlock(src, off, rk) {
    var b = new Uint8Array(BS), t = new Uint8Array(BS), i, r;
    for (i = 0; i < BS; i++) b[i] = src[off + i];
    for (i = 0; i < BS; i++) b[i] ^= rk[ROUNDS][i];
    for (r = ROUNDS - 1; r >= 0; r--) {
      for (i = 0; i < BS; i++) t[PERM[i]] = b[i];
      b.set(t);
      unmix(b);
      for (i = 0; i < BS; i++) b[i] = INV_SBOX[b[i]] ^ rk[r][i];
    }
    return b;
  }

  function keyFrom(seed) {
    var r = lcg(seed), rk = [], k, i, a;
    for (k = 0; k <= ROUNDS; k++) {
      a = new Uint8Array(BS);
      for (i = 0; i < BS; i++) a[i] = (r() >>> 21) & 255;
      rk.push(a);
    }
    return rk;
  }

  function ivFrom(seed) {
    var r = lcg((seed ^ 0x9E3779B9) >>> 0), a = new Uint8Array(BS), i;
    for (i = 0; i < BS; i++) a[i] = (r() >>> 21) & 255;
    return a;
  }

  /* ECB: C_i = E(P_i). No state between blocks — that is the whole bug. */
  function ecbEncrypt(p, rk) {
    var out = new Uint8Array(p.length), off;
    for (off = 0; off < p.length; off += BS) out.set(encBlock(p, off, rk), off);
    return out;
  }

  /* CBC: C_i = E(P_i XOR C_(i-1)), with C_(-1) = IV. */
  function cbcEncrypt(p, rk, iv) {
    var out = new Uint8Array(p.length), x = new Uint8Array(BS), prev = iv, c, off, i;
    for (off = 0; off < p.length; off += BS) {
      for (i = 0; i < BS; i++) x[i] = p[off + i] ^ prev[i];
      c = encBlock(x, 0, rk);
      out.set(c, off);
      prev = c;
    }
    return out;
  }

  /* CBC decrypt: P_i = D(C_i) XOR C_(i-1). Note what this says about tampering:
   * P_i depends on C_(i-1) by a plain XOR, so an attacker who changes one byte
   * of C_(i-1) changes exactly that byte of P_i, by exactly that XOR. */
  function cbcDecrypt(c, rk, iv) {
    var out = new Uint8Array(c.length), prev = iv, d, off, i;
    for (off = 0; off < c.length; off += BS) {
      d = decBlock(c, off, rk);
      for (i = 0; i < BS; i++) out[off + i] = d[i] ^ prev[i];
      prev = c.subarray(off, off + BS);
    }
    return out;
  }

  /* Which ciphertext blocks are byte-for-byte repeats of another block. */
  function blockInfo(c) {
    var n = c.length / BS, seen = Object.create(null), dup = new Uint8Array(n);
    var distinct = 0, i, j, k, s;
    for (i = 0; i < n; i++) {
      s = "";
      for (j = 0; j < BS; j++) s += String.fromCharCode(c[i * BS + j]);
      if (s in seen) { dup[i] = 1; dup[seen[s]] = 1; }
      else { seen[s] = i; distinct++; }
    }
    k = 0;
    for (i = 0; i < n; i++) if (dup[i]) k++;
    return { distinct: distinct, repeated: k, total: n };
  }

  /* The picture. Flat regions on purpose: that is what ECB preserves.
   * Palette index lives in the top two bits of the byte, so plaintext and
   * ciphertext can be drawn through the exact same 4-colour rule. */
  var PAL = [0x00, 0x55, 0xAA, 0xFF];   // >>6 gives 0,1,2,3

  function inRoundRect(x, y, x0, y0, x1, y1, r) {
    if (x < x0 || x >= x1 || y < y0 || y >= y1) return false;
    var cx = x < x0 + r ? x0 + r : (x > x1 - 1 - r ? x1 - 1 - r : x);
    var cy = y < y0 + r ? y0 + r : (y > y1 - 1 - r ? y1 - 1 - r : y);
    var dx = x - cx, dy = y - cy;
    return dx * dx + dy * dy <= r * r;
  }

  function buildImage() {
    var img = new Uint8Array(W * H), x, y, i, dx, dy, d2, hw;
    for (y = 0; y < H; y++) {
      for (x = 0; x < W; x++) {
        i = 0;                                   // background
        dx = x - 64; dy = y - 42; d2 = dx * dx + dy * dy;
        if (y <= 42 && d2 <= 24 * 24 && d2 >= 15 * 15) i = 2;   // shackle
        if (inRoundRect(x, y, 30, 44, 98, 88, 10)) {
          i = 1;                                 // body
          dx = x - 64; dy = y - 60;
          if (dx * dx + dy * dy <= 7 * 7) i = 3;                // keyhole bowl
          hw = 2 + ((y - 60) * 5) / 18;
          if (y >= 60 && y < 78 && x >= 64 - hw && x <= 64 + hw) i = 3;  // stem
        }
        img[y * W + x] = PAL[i];
      }
    }
    return img;
  }

  function strBytes(s) {
    var a = new Uint8Array(s.length), i;
    for (i = 0; i < s.length; i++) a[i] = s.charCodeAt(i) & 255;
    return a;
  }

  function hex(b) { return (b < 16 ? "0" : "") + b.toString(16); }

  function printable(b) {
    return (b >= 32 && b < 127) ? String.fromCharCode(b) : "·";
  }

  /* ===== CORE END ===== */

  /* -------- rendering -------- */

  var RGB = [[255, 255, 255], [227, 82, 5], [1, 123, 196], [22, 25, 29]];

  var KEY_SEEDS = [0x1A2B3C4D, 0x51EEDBEE, 0x0BADCAFE, 0x2468ACE0, 0x7E57C0DE];

  var img = buildImage();
  var tokenBytes = strBytes(TOKEN);

  var st = { keyIx: 0, map: false, target: "c0", byte: -1, bit: -1 };
  var rk, iv, tokIv, ecbC, cbcC, ecbInfo, cbcInfo, tokC;

  function el(id) { return document.getElementById(id); }

  function paintBytes(canvas, bytes) {
    var ctx = canvas.getContext("2d"), d = ctx.createImageData(W, H), p = d.data;
    var i, c;
    for (i = 0; i < W * H; i++) {
      c = RGB[bytes[i] >> 6];
      p[i * 4] = c[0]; p[i * 4 + 1] = c[1]; p[i * 4 + 2] = c[2]; p[i * 4 + 3] = 255;
    }
    ctx.putImageData(d, 0, 0);
  }

  /* Block-identity map: paint each 16-byte ciphertext block one flat colour
   * derived from its bytes, so "same colour" means "byte-identical block".
   *
   * This replaced a two-colour repeat/unique map, which was truthful but said
   * almost nothing on screen: 754 of 768 ECB blocks repeat, so it was a solid
   * rectangle with a few stray marks. Colouring by identity instead makes the
   * actual claim visible — under ECB the drawing reappears out of block equality
   * alone, under CBC every block gets its own colour. */
  function hsl(h, s, l) {
    var c = (1 - Math.abs(2 * l - 1)) * s, x = c * (1 - Math.abs((h / 60) % 2 - 1));
    var m = l - c / 2, r = 0, g = 0, b = 0;
    if (h < 60) { r = c; g = x; }
    else if (h < 120) { r = x; g = c; }
    else if (h < 180) { g = c; b = x; }
    else if (h < 240) { g = x; b = c; }
    else if (h < 300) { r = x; b = c; }
    else { r = c; b = x; }
    return [Math.round((r + m) * 255), Math.round((g + m) * 255), Math.round((b + m) * 255)];
  }

  function paintIdentity(canvas, ct) {
    var ctx = canvas.getContext("2d"), d = ctx.createImageData(W, H), p = d.data;
    var nb = ct.length / BS, cols = [], bi, i, h, c;
    for (bi = 0; bi < nb; bi++) {
      h = 2166136261;
      for (i = 0; i < BS; i++) { h ^= ct[bi * BS + i]; h = Math.imul(h, 16777619); }
      cols.push(hsl((h >>> 0) % 360, 0.62, 0.55));
    }
    for (i = 0; i < W * H; i++) {
      c = cols[(i / BS) | 0];
      p[i * 4] = c[0]; p[i * 4 + 1] = c[1]; p[i * 4 + 2] = c[2]; p[i * 4 + 3] = 255;
    }
    ctx.putImageData(d, 0, 0);
  }

  function txt(node, s) { node.textContent = s; }

  /* A canvas is opaque to assistive tech, so aria-label is the ONLY description
   * of it — which means it has to move when the picture does. The map toggle
   * repaints both ciphertext canvases into a completely different kind of
   * image, and a label still saying "the padlock is still visible" would be
   * describing a view that is no longer on screen. */
  function describe(id, s) { el(id).setAttribute("aria-label", s); }

  /* -------- panel 1 -------- */

  function rekey() {
    var seed = KEY_SEEDS[st.keyIx % KEY_SEEDS.length];
    rk = keyFrom(seed);
    iv = ivFrom(seed);
    /* The token gets its OWN IV, not the picture's. The two panels are two
     * different messages under one key, and reusing an IV across messages is a
     * separate bug from the one this page is teaching — under CBC it leaks
     * whether two messages share a leading block. A page that says "use a fresh
     * IV per message" in Week 3 and then does not is teaching the wrong habit to
     * anyone who reads the source, so panel 2 keys off a distinct derivation. */
    tokIv = ivFrom((seed ^ 0xA5A5A5A5) >>> 0);
    ecbC = ecbEncrypt(img, rk);
    cbcC = cbcEncrypt(img, rk, iv);
    ecbInfo = blockInfo(ecbC);
    cbcInfo = blockInfo(cbcC);
    tokC = cbcEncrypt(tokenBytes, rk, tokIv);
  }

  function drawPanel1() {
    paintBytes(el("cvPlain"), img);
    if (st.map) {
      paintIdentity(el("cvEcb"), ecbC);
      paintIdentity(el("cvCbc"), cbcC);
      txt(el("capEcb"), "ECB — block-identity map");
      txt(el("capCbc"), "CBC — block-identity map");
      describe("cvEcb", "ECB block-identity map: each 16-byte ciphertext block "
        + "painted one flat colour computed from its own bytes. The padlock "
        + "reappears, in " + ecbInfo.distinct + " colours over " + NB
        + " blocks, because equal plaintext blocks give equal ciphertext blocks.");
      describe("cvCbc", "CBC block-identity map: " + cbcInfo.distinct
        + " colours over " + NB + " blocks — every block is unique, so the map "
        + "is unstructured speckle and no shape appears.");
      txt(el("statEcb"), ecbInfo.distinct + " colours for " + NB + " blocks");
      txt(el("statCbc"), cbcInfo.distinct + " colours for " + NB + " blocks");
      el("mapToggle").textContent = "✓ Block-identity map (click for ciphertext)";
      el("mapToggle").setAttribute("aria-pressed", "true");
      el("imgWhy").textContent =
        "Now each 16-byte ciphertext block is painted one flat colour computed "
        + "from its own bytes, so same colour means byte-identical block. ECB: "
        + ecbInfo.distinct + " colours for " + NB + " blocks, and the drawing comes "
        + "back — it can be recovered from block equality alone, without breaking "
        + "the cipher. " + ecbInfo.repeated + " of the " + NB + " blocks are exact "
        + "repeats of another block. CBC: " + cbcInfo.distinct + " colours for "
        + NB + " blocks. Nothing repeats, so there is nothing to reconstruct.";
    } else {
      paintBytes(el("cvEcb"), ecbC);
      paintBytes(el("cvCbc"), cbcC);
      txt(el("capEcb"), "ECB ciphertext");
      txt(el("capCbc"), "CBC ciphertext");
      describe("cvEcb", "ECB ciphertext drawn through the same 4-colour palette "
        + "as the plaintext. The padlock outline is still legible: each flat "
        + "region became one repeated 16-pixel pattern.");
      describe("cvCbc", "CBC ciphertext drawn through the same 4-colour palette. "
        + "Uniform noise — no outline, no regions, nothing of the padlock left.");
      txt(el("statEcb"), ecbInfo.distinct + " distinct blocks of " + NB);
      txt(el("statCbc"), cbcInfo.distinct + " distinct blocks of " + NB);
      el("mapToggle").textContent = "Show block-identity map";
      el("mapToggle").setAttribute("aria-pressed", "false");
      el("imgWhy").textContent =
        "Same key, same picture, same 4-colour palette for drawing every byte. "
        + "ECB: " + ecbInfo.distinct + " distinct blocks out of " + NB
        + " — each flat region encrypts to one repeated 16-pixel pattern, so the "
        + "outline is still there. CBC: " + cbcInfo.distinct + " distinct blocks "
        + "out of " + NB + " — nothing repeats, so there is no structure left to see.";
    }
    txt(el("statPlain"), ecbInfo.total + " blocks of 16 bytes, 4 colours");
  }

  /* -------- panel 2 -------- */

  function maskByte() { return st.bit < 0 ? 0 : (1 << st.bit); }

  function tamperedIv() {
    var a = new Uint8Array(tokIv);
    if (st.target === "iv" && st.byte >= 0 && st.bit >= 0) a[st.byte] ^= maskByte();
    return a;
  }

  function tamperedCt() {
    var a = new Uint8Array(tokC);
    if (st.target === "c0" && st.byte >= 0 && st.bit >= 0) a[st.byte] ^= maskByte();
    return a;
  }

  function cellRow(host, values, target) {
    host.innerHTML = "";
    var i, cell, ch, mk;
    for (i = 0; i < BS; i++) {
      cell = document.createElement(target ? "button" : "span");
      cell.className = "aes-modes-cell";
      if (target) {
        cell.type = "button";
        cell.className += " aes-modes-hit";
        cell.setAttribute("data-i", String(i));
        cell.setAttribute("aria-pressed",
          (st.target === target && st.byte === i) ? "true" : "false");
        if (st.target === target && st.byte === i) cell.className += " aes-modes-sel";
        cell.setAttribute("aria-label", target.toUpperCase() + " byte " + i);
      }
      ch = document.createElement("span");
      ch.className = "aes-modes-ch";
      ch.textContent = values[i].text;
      mk = document.createElement("span");
      mk.className = "aes-modes-mk";
      mk.textContent = values[i].mark || " ";
      if (values[i].changed) cell.className += " aes-modes-chg";
      cell.appendChild(ch);
      cell.appendChild(mk);
      host.appendChild(cell);
    }
  }

  /* `↯` is the only marker, and it is enough: selecting a byte always applies a
   * flip (rowClick forces a bit, bitButton forces a byte), and XOR with a
   * non-zero mask always changes the value — so on the row being tampered the
   * changed byte IS the selected byte. An earlier "▲ = selected but not yet
   * flipped" state was unreachable and unexplained by the legend below the
   * rows, which names only ↯ and ·. Selection is additionally carried by
   * aria-pressed and a class, so it is never signalled by colour alone. */
  function hexCells(bytes, base) {
    var out = [], i, changed;
    for (i = 0; i < BS; i++) {
      changed = base ? bytes[i] !== base[i] : false;
      out.push({ text: hex(bytes[i]), mark: changed ? "↯" : "", changed: changed });
    }
    return out;
  }

  function charCells(bytes, base) {
    var out = [], i, changed;
    for (i = 0; i < BS; i++) {
      changed = bytes[i] !== base[i];
      out.push({ text: printable(bytes[i]), mark: changed ? "↯" : "", changed: changed });
    }
    return out;
  }

  function countDiff(a, b) {
    var n = 0, i;
    for (i = 0; i < BS; i++) if (a[i] !== b[i]) n++;
    return n;
  }

  function tokenText(bytes) {
    var s = "", i;
    for (i = 0; i < bytes.length; i++) s += printable(bytes[i]);
    return s;
  }

  function drawPanel2() {
    var iv2 = tamperedIv(), ct2 = tamperedCt();
    var clean = cbcDecrypt(tokC, rk, tokIv);
    var out = cbcDecrypt(ct2, rk, iv2);

    var p0 = out.subarray(0, BS), p1 = out.subarray(BS, 2 * BS);
    var b0 = clean.subarray(0, BS), b1 = clean.subarray(BS, 2 * BS);

    cellRow(el("ivRow"), hexCells(iv2, tokIv), "iv");
    cellRow(el("c0Row"), hexCells(ct2.subarray(0, BS), tokC.subarray(0, BS)), "c0");
    cellRow(el("c1Row"), hexCells(ct2.subarray(BS, 2 * BS), null), null);
    cellRow(el("p0Row"), charCells(p0, b0), null);
    cellRow(el("p1Row"), charCells(p1, b1), null);

    txt(el("tokenPlain"), "P0 = \"" + TOKEN.slice(0, BS) + "\"   P1 = \"" + TOKEN.slice(BS) + "\"");
    txt(el("tokenOut"), "decrypts to: \"" + tokenText(out) + "\"");

    var d0 = countDiff(p0, b0), d1 = countDiff(p1, b1);
    var lab = el("tamperLabel"), why = el("flipWhy");
    why.innerHTML = "";

    if (st.byte < 0 || st.bit < 0) {
      lab.className = "verdict ok";
      lab.textContent = "Nothing tampered yet — the token decrypts to itself.";
      addP(why, "Pick a byte in the IV row or the C0 row, then pick a bit. "
        + "Both rows travel on the wire in the clear, so both are things an "
        + "attacker can change. Nothing here is encrypted twice and nothing is signed.");
      return;
    }

    var tgt = st.target === "iv" ? "IV" : "C0";
    lab.className = "verdict bad";
    lab.textContent = "Flipped bit " + st.bit + " (XOR 0x" + hex(maskByte())
      + ") of " + tgt + " byte " + st.byte + ".";

    if (st.target === "c0") {
      addP(why, "P0 = D(C0) ⊕ IV. C0 changed, so D(C0) is scrambled: "
        + d0 + " of 16 bytes of block 0 are now garbage. That is the cost, and it "
        + "is why the attack needs a block it is willing to destroy.");
      addP(why, "P1 = D(C1) ⊕ C0. C1 was never touched, so D(C1) is unchanged — "
        + "and C0 enters by a plain XOR. Flipping one bit of C0 flips exactly that "
        + "bit of P1: " + d1 + " byte changed, byte " + st.byte + ", “"
        + printable(b1[st.byte]) + "” → “" + printable(p1[st.byte]) + "”.");
    } else {
      addP(why, "P0 = D(C0) ⊕ IV, and the IV is not secret — it ships with the "
        + "message. Changing it does not scramble anything: " + d0
        + " byte changed in block 0, byte " + st.byte + ", “"
        + printable(b0[st.byte]) + "” → “" + printable(p0[st.byte]) + "”.");
      addP(why, "P1 = D(C1) ⊕ C0, and neither C1 nor C0 moved, so block 1 is "
        + "untouched (" + d1 + " bytes changed). Block 0 is the one block that "
        + "costs nothing to edit: the IV is not a ciphertext block, so nothing "
        + "is decrypted from it and there is no garbage to pay. Every later "
        + "block is edited through the block before it — which is why preset 4 "
        + "destroys block 0 to reach block 1.");
    }
    addP(why, "None of this needs the key. CBC gives confidentiality and nothing "
      + "else: there is no integrity check, so the server cannot tell an edited "
      + "ciphertext from a genuine one. That is what a MAC — or AES-GCM — is for.");
  }

  function addP(host, s) {
    var p = document.createElement("p");
    p.textContent = s;
    host.appendChild(p);
  }

  /* -------- controls -------- */

  function rowClick(ev, target) {
    var b = ev.target;
    while (b && b !== ev.currentTarget && !b.hasAttribute("data-i")) b = b.parentNode;
    if (!b || !b.hasAttribute("data-i")) return;
    var i = parseInt(b.getAttribute("data-i"), 10);
    /* Clicking the selected byte again clears the tamper. The bit row has to be
     * rebuilt too, or it keeps showing a pressed bit that no longer does
     * anything — a control claiming a state the page has just denied. */
    if (st.target === target && st.byte === i) { st.byte = -1; st.bit = -1; }
    else { st.target = target; st.byte = i; if (st.bit < 0) st.bit = 0; }
    buildBitButtons();
    drawPanel2();
    focusCell(target, i);   // the row was rebuilt; put focus back where it was
  }

  function focusCell(target, i) {
    if (i < 0) return;
    var row = el(target === "iv" ? "ivRow" : "c0Row");
    var b = row.querySelector('[data-i="' + i + '"]');
    if (b) b.focus();
  }

  /* Arrow keys walk a row: 32 tab stops is a lot to page through on stage. */
  function rowKeys(ev) {
    var d = ev.key === "ArrowRight" ? 1 : (ev.key === "ArrowLeft" ? -1 : 0);
    if (!d) return;
    var b = ev.target;
    if (!b.hasAttribute || !b.hasAttribute("data-i")) return;
    var i = parseInt(b.getAttribute("data-i"), 10) + d;
    if (i < 0 || i >= BS) return;
    ev.preventDefault();
    var n = ev.currentTarget.querySelector('[data-i="' + i + '"]');
    if (n) n.focus();
  }

  function buildBitButtons() {
    var host = el("bitRow"), i;
    host.innerHTML = "";
    var none = document.createElement("button");
    none.type = "button";
    none.textContent = (st.bit < 0 ? "✓ " : "") + "no flip";
    /* Same group, same semantics as the eight bit buttons: without this the
     * only unpressed-by-default member of the group reports no toggle state at
     * all, and a screen reader cannot tell that "no flip" is the current one. */
    none.setAttribute("aria-pressed", st.bit < 0 ? "true" : "false");
    if (st.bit < 0) none.className = "aes-modes-on";
    none.addEventListener("click", function () {
      st.bit = -1; st.byte = -1; buildBitButtons(); drawPanel2();
    });
    host.appendChild(none);
    for (i = 7; i >= 0; i--) {
      host.appendChild(bitButton(i));
    }
  }

  function bitButton(i) {
    var b = document.createElement("button");
    b.type = "button";
    b.textContent = (st.bit === i ? "✓ " : "") + "bit " + i + " (" + (1 << i) + ")";
    b.setAttribute("aria-pressed", st.bit === i ? "true" : "false");
    if (st.bit === i) b.className = "aes-modes-on";
    b.addEventListener("click", function () {
      st.bit = i;
      if (st.byte < 0) st.byte = 0;
      buildBitButtons();
      drawPanel2();
    });
    return b;
  }

  var PRESETS = [
    {
      label: "1 · The picture",
      go: function () { st.map = false; drawPanel1(); return "p1"; }
    },
    {
      label: "2 · Same block, same colour",
      go: function () { st.map = true; drawPanel1(); return "p1"; }
    },
    {
      /* Deliberately does NOT reset st.map. The claim is "same leak", and the
       * evidence for it is the identity map showing the same colour count under
       * a different key — so if the student got here from preset 2, keep the
       * view they are comparing against instead of throwing it away. */
      label: "3 · New key, same leak",
      go: function () {
        st.keyIx++; rekey(); drawPanel1(); drawPanel2(); return "p1";
      }
    },
    {
      /* Byte 12 of block 1 is the "0" of "admin=0" (token index 28). Bit 0
       * takes 0x30 to 0x31 — privilege escalation by one XOR, no key. */
      label: "4 · Token: admin=0 → admin=1",
      go: function () {
        st.target = "c0"; st.byte = 12; st.bit = 0;
        buildBitButtons(); drawPanel2(); return "p2";
      }
    },
    {
      /* The contrast to preset 4: byte 5 of block 0 is the "8" of the session
       * id, and editing it through the IV costs nothing at all. Framed as "no
       * garbage" rather than "forge a session id" on purpose — the transferable
       * point is that block 0 is free, not that mangling a session id is a
       * generally useful attack. */
      label: "5 · Token: edit block 0 with no garbage",
      go: function () {
        st.target = "iv"; st.byte = 5; st.bit = 0;
        buildBitButtons(); drawPanel2(); return "p2";
      }
    }
  ];

  function init() {
    var host = el("presets");
    PRESETS.forEach(function (p) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = p.label;
      b.addEventListener("click", function () {
        var where = p.go();
        var card = el(where === "p1" ? "panel1" : "panel2");
        if (card && card.scrollIntoView) card.scrollIntoView({ block: "nearest" });
      });
      host.appendChild(b);
    });

    el("newKey").addEventListener("click", function () {
      st.keyIx++; rekey(); drawPanel1(); drawPanel2();
    });
    el("mapToggle").addEventListener("click", function () {
      st.map = !st.map; drawPanel1();
    });
    el("ivRow").addEventListener("click", function (e) { rowClick(e, "iv"); });
    el("c0Row").addEventListener("click", function (e) { rowClick(e, "c0"); });
    el("ivRow").addEventListener("keydown", rowKeys);
    el("c0Row").addEventListener("keydown", rowKeys);

    rekey();
    drawPanel1();
    buildBitButtons();
    drawPanel2();
  }

  init();
})();

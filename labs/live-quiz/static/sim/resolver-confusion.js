/* resolver-confusion.js — Week 12 simulation.
 *
 * WHAT THIS IS FOR
 * Task 2's whole exercise is watching the wrong package win, and Task 4's
 * defense #2 is "single trusted index... explain why the resolver stops
 * shopping around" — this computes that resolver choice live from whatever
 * versions and index mode are set, rather than asserting the outcome.
 *
 * The rule is dependency-confusion.md's own, not invented: in single-index
 * mode the resolver only ever sees the ONE configured index, full stop — the
 * public package is never in the running, regardless of its version. In
 * merged (--extra-index-url) mode, the resolver compares versions from BOTH
 * indexes and installs whichever number is higher, with no notion of
 * "trusted source." That second rule is also why relying on "keep your
 * internal version number high" is not a real defense — try setting the
 * public version below the private one, then remember the attacker picks
 * their own number.
 *
 * Version comparison is real (numeric, dotted, PEP 440-shaped enough for
 * these examples) — not string comparison, which would get "99.0.0" vs
 * "1.4.0" right by accident but "1.10.0" vs "1.9.0" wrong.
 */
(function () {
  "use strict";

  var PRESETS = [
    { label: "the attack", priv: "1.4.0", pub: "99.0.0", mode: "merged" },
    { label: "single-index defense", priv: "1.4.0", pub: "99.0.0", mode: "single" },
    { label: "“win the race” (unreliable)", priv: "2.0.0", pub: "1.9.0", mode: "merged" }
  ];

  function parseVersion(v) {
    var parts = String(v || "0").trim().split(".");
    var nums = [];
    for (var i = 0; i < parts.length; i++) {
      var n = parseInt(parts[i], 10);
      nums.push(isNaN(n) ? 0 : n);
    }
    return nums;
  }

  function compareVersions(a, b) {
    var pa = parseVersion(a), pb = parseVersion(b);
    var len = Math.max(pa.length, pb.length);
    for (var i = 0; i < len; i++) {
      var na = pa[i] || 0, nb = pb[i] || 0;
      if (na !== nb) return na - nb;
    }
    return 0;
  }

  var privInput = document.getElementById("priv");
  var pubInput = document.getElementById("pub");
  var modeSingle = document.getElementById("mode-single");
  var modeMerged = document.getElementById("mode-merged");
  var presetsEl = document.getElementById("presets");
  var verdictEl = document.getElementById("verdict");
  var explainEl = document.getElementById("explain");
  var privCardEl = document.getElementById("priv-card");
  var pubCardEl = document.getElementById("pub-card");

  function update() {
    var priv = privInput.value || "0.0.0";
    var pub = pubInput.value || "0.0.0";
    var merged = modeMerged.checked;

    var wins, source;
    if (!merged) {
      // Single index: the public index is never queried at all.
      wins = "priv";
      source = "private index — the only one configured";
    } else if (compareVersions(pub, priv) > 0) {
      wins = "pub";
      source = "public index — higher version number";
    } else {
      wins = "priv";
      source = "private index — its version is not lower";
    }

    privCardEl.className = "resolver-confusion-card" + (wins === "priv" ? " is-picked" : "");
    pubCardEl.className = "resolver-confusion-card" + (wins === "pub" ? " is-picked" : "");

    if (!merged) {
      verdictEl.className = "verdict ok";
      verdictEl.textContent = "installs acme-internal-utils " + priv + " — safe";
      explainEl.textContent = "--index-url means exactly one index is configured. The "
        + "resolver has no second registry to compare against, so the public "
        + "look-alike is never even fetched, let alone considered — its version "
        + "number doesn't matter here at all.";
    } else if (wins === "pub") {
      verdictEl.className = "verdict bad";
      verdictEl.textContent = "installs acme-internal-utils " + pub + " from PUBLIC — confused";
      explainEl.textContent = "--extra-index-url merges both registries into one pool, and "
        + "the resolver's only rule is “highest version wins” — it has no concept "
        + "of which source is trusted. " + pub + " > " + priv + ", so the attacker's "
        + "package installs and its setup.py runs as you.";
    } else {
      verdictEl.className = "verdict ok";
      verdictEl.textContent = "installs acme-internal-utils " + priv + " from PRIVATE — safe this time";
      explainEl.textContent = "Even merged, the private version isn't lower, so it still wins "
        + "the comparison. But this is NOT a defense — the attacker chooses their own "
        + "version number and will simply publish something higher. Raise the public "
        + "version above " + priv + " and watch it flip.";
    }
  }

  PRESETS.forEach(function (p) {
    var b = document.createElement("button");
    b.type = "button";
    b.textContent = p.label;
    b.addEventListener("click", function () {
      privInput.value = p.priv;
      pubInput.value = p.pub;
      if (p.mode === "single") { modeSingle.checked = true; } else { modeMerged.checked = true; }
      update();
    });
    presetsEl.appendChild(b);
  });

  privInput.addEventListener("input", update);
  pubInput.addEventListener("input", update);
  modeSingle.addEventListener("change", update);
  modeMerged.addEventListener("change", update);
  update();
})();

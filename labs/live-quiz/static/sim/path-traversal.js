/* path-traversal.js — Week 1 simulation.
 *
 * WHAT THIS IS FOR
 * The worksheet's Task 3 finding is a WRITE bug, not a read bug, and that
 * direction is easy to get backwards under exam pressure. This simulation
 * runs the same naive path-join the sample app uses, live, against whatever
 * the student types — so "resolves outside uploads/" is something they watch
 * happen, not a claim they take on faith. The read side runs the SAME input
 * through Werkzeug's safe_join logic, so the asymmetry (identical input,
 * opposite outcome) is the thing on screen, not just the thing in the slide.
 *
 * Path resolution is real ".." collapsing on a POSIX-style path, computed
 * locally. No request is ever sent anywhere.
 */
(function () {
  "use strict";

  var BASE = "/app/uploads";

  var PRESETS = [
    { label: "profile.jpg", v: "profile.jpg" },
    { label: "../../escaped.txt", v: "../../escaped.txt" },
    { label: "../../../../etc/passwd", v: "../../../../etc/passwd" }
  ];

  function resolvePath(base, name) {
    var raw = (base + "/" + String(name || "")).split("/");
    var stack = [];
    for (var i = 0; i < raw.length; i++) {
      var part = raw[i];
      if (part === "" || part === ".") continue;
      if (part === "..") { stack.pop(); continue; }
      stack.push(part);
    }
    return "/" + stack.join("/");
  }

  function isInside(base, resolved) {
    return resolved === base || resolved.indexOf(base + "/") === 0;
  }

  var input = document.getElementById("fn");
  var presetsEl = document.getElementById("presets");
  var resolvedEl = document.getElementById("resolved");
  var wverdict = document.getElementById("wverdict");
  var wexplain = document.getElementById("wexplain");
  var rverdict = document.getElementById("rverdict");
  var rexplain = document.getElementById("rexplain");

  var svg = document.getElementById("dfd");
  var NS = "http://www.w3.org/2000/svg";
  var BROWSER = { x: 20, y: 130, w: 100, h: 42 };
  var FLASK = { x: 185, y: 130, w: 100, h: 42 };
  var STORE = { x: 340, y: 46, w: 100, h: 46 };

  function el(name, attrs, text) {
    var e = document.createElementNS(NS, name);
    Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (text != null) e.textContent = text;
    return e;
  }

  function drawStatic() {
    svg.appendChild(el("line", {
      x1: 152, y1: 16, x2: 152, y2: 210, class: "path-traversal-boundary"
    }));
    svg.appendChild(el("text", {
      x: 152, y: 12, class: "path-traversal-boundarylabel", "text-anchor": "middle"
    }, "INTERNET → APP"));

    svg.appendChild(el("rect", {
      x: BROWSER.x, y: BROWSER.y, width: BROWSER.w, height: BROWSER.h, rx: 6,
      class: "box box-actor"
    }));
    svg.appendChild(el("text", {
      x: BROWSER.x + BROWSER.w / 2, y: BROWSER.y + BROWSER.h / 2 + 5,
      class: "boxlabel", "text-anchor": "middle"
    }, "Browser"));

    svg.appendChild(el("rect", {
      x: FLASK.x, y: FLASK.y, width: FLASK.w, height: FLASK.h, rx: 6, class: "box"
    }));
    svg.appendChild(el("text", {
      x: FLASK.x + FLASK.w / 2, y: FLASK.y + FLASK.h / 2 + 5,
      class: "boxlabel", "text-anchor": "middle"
    }, "Flask app"));

    svg.appendChild(el("rect", {
      x: STORE.x, y: STORE.y, width: STORE.w, height: STORE.h, rx: 6,
      class: "box box-store", id: "store-box"
    }));
    svg.appendChild(el("text", {
      x: STORE.x + STORE.w / 2, y: STORE.y + STORE.h / 2 + 4,
      class: "boxlabel", "text-anchor": "middle"
    }, "uploads/"));

    svg.appendChild(el("line", {
      x1: BROWSER.x + BROWSER.w, y1: BROWSER.y + 14,
      x2: FLASK.x, y2: FLASK.y + 14, class: "edge"
    }));
    svg.appendChild(el("text", {
      x: (BROWSER.x + BROWSER.w + FLASK.x) / 2, y: BROWSER.y + 4,
      class: "edgelabel", "text-anchor": "middle"
    }, "POST /upload"));

    svg.appendChild(el("line", {
      x1: FLASK.x, y1: FLASK.y + 30,
      x2: BROWSER.x + BROWSER.w, y2: BROWSER.y + 30, class: "edge"
    }));
    svg.appendChild(el("text", {
      x: (BROWSER.x + BROWSER.w + FLASK.x) / 2, y: BROWSER.y + BROWSER.h + 16,
      class: "edgelabel", "text-anchor": "middle"
    }, "GET /files/<name>"));
  }

  var writeMark = null, readMark = null;

  function setWriteMark(inside) {
    if (writeMark) { svg.removeChild(writeMark); writeMark = null; }
    writeMark = el("g", { class: "path-traversal-mark" });
    if (inside) {
      writeMark.appendChild(el("circle", {
        cx: STORE.x + STORE.w / 2, cy: STORE.y + STORE.h + 14, r: 5,
        class: "path-traversal-dot is-ok"
      }));
    } else {
      var x = FLASK.x + FLASK.w / 2, y = FLASK.y + FLASK.h + 34;
      writeMark.appendChild(el("circle", { cx: x, cy: y, r: 5, class: "path-traversal-dot is-bad" }));
      writeMark.appendChild(el("text", {
        x: x, y: y + 18, class: "path-traversal-marklabel", "text-anchor": "middle"
      }, "written outside uploads/"));
    }
    svg.appendChild(writeMark);
  }

  function setReadMark(inside) {
    if (readMark) { svg.removeChild(readMark); readMark = null; }
    var x = STORE.x + STORE.w / 2, y = STORE.y - 14;
    readMark = el("g", { class: "path-traversal-mark", transform: "translate(" + x + "," + y + ")" });
    if (inside) {
      readMark.appendChild(el("circle", { r: 9, class: "path-traversal-badge is-ok" }));
      readMark.appendChild(el("path", { d: "M-4,0 L-1,4 L5,-4", class: "path-traversal-glyph" }));
    } else {
      readMark.appendChild(el("circle", { r: 9, class: "path-traversal-badge is-ok" }));
      readMark.appendChild(el("line", { x1: -4, y1: -4, x2: 4, y2: 4, class: "path-traversal-glyph" }));
      readMark.appendChild(el("line", { x1: 4, y1: -4, x2: -4, y2: 4, class: "path-traversal-glyph" }));
    }
    svg.appendChild(readMark);
  }

  function update() {
    var name = input.value;
    var resolved = resolvePath(BASE, name);
    var inside = isInside(BASE, resolved);
    resolvedEl.textContent = resolved;

    setWriteMark(inside);
    setReadMark(inside);

    if (inside) {
      wverdict.className = "verdict ok";
      wverdict.textContent = "lands inside uploads/ — looks fine";
      wexplain.textContent = "No bounds check runs on this path regardless of the "
        + "outcome — this particular filename just happens to resolve inside "
        + "uploads/. That is the trap: the code that ran is identical either way, "
        + "so a different filename is all it takes.";
    } else {
      wverdict.className = "verdict bad";
      wverdict.textContent = "writes outside uploads/ — CWE-501";
      wexplain.textContent = "The filename is attacker-controlled and unsanitized on "
        + "save. This resolves outside uploads/ — arbitrary-file-write, "
        + "unauthenticated, anywhere the process can reach.";
    }

    rverdict.className = "verdict ok";
    if (inside) {
      rverdict.textContent = "served";
      rexplain.textContent = "Resolves inside uploads/, so Werkzeug's safe_join lets "
        + "it through — this is what the read path is supposed to do for a "
        + "legitimate filename.";
    } else {
      rverdict.textContent = "blocked (403)";
      rexplain.textContent = "safe_join resolves the same path, notices it falls "
        + "outside uploads/, and refuses it before ever touching the filesystem. "
        + "Same input as the write side, opposite outcome.";
    }
  }

  drawStatic();
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

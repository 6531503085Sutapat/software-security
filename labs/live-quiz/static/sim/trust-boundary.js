/* trust-boundary.js — Week 1 simulation.
 *
 * WHY THIS EXISTS, SPECIFICALLY
 * Joshi et al. (ASEE 2024) found students taught STRIDE alone "discounted
 * system-level threats" — they enumerate per component and stop. This
 * simulation is built to make the system level the thing you cannot miss: you
 * toggle a component to "attacker owns it" and the diagram shows what that
 * REACHES, not just what it is.
 *
 * The chain panel is the whole point. Two threats the per-component table would
 * both mark "low" combine into a path to the data store, and the simulation
 * draws that path.
 *
 * No dependencies, no inline handlers (the page CSP is script-src 'self' with
 * no unsafe-inline), no network. Everything is addEventListener + SVG.
 */
(function () {
  "use strict";

  // A deliberately ordinary web app — the same shape as the Week 1 sample app.
  var NODES = [
    { id: "browser", label: "Browser", kind: "actor", zone: "public", x: 60, y: 150 },
    { id: "cdn", label: "CDN / static", kind: "proc", zone: "public", x: 210, y: 60 },
    { id: "api", label: "API server", kind: "proc", zone: "app", x: 340, y: 150 },
    { id: "auth", label: "Auth service", kind: "proc", zone: "app", x: 340, y: 262 },
    { id: "db", label: "User DB", kind: "store", zone: "data", x: 560, y: 150 },
    { id: "logs", label: "Log store", kind: "store", zone: "data", x: 560, y: 262 }
  ];

  var EDGES = [
    { from: "browser", to: "cdn", label: "GET assets" },
    { from: "browser", to: "api", label: "JSON + session cookie" },
    { from: "api", to: "auth", label: "verify token" },
    { from: "api", to: "db", label: "SQL" },
    { from: "auth", to: "db", label: "SQL" },
    { from: "api", to: "logs", label: "write" }
  ];

  var ZONES = [
    { id: "public", label: "Untrusted — public internet", x: 20, y: 20, w: 260, h: 300 },
    { id: "app", label: "Application tier", x: 292, y: 20, w: 190, h: 300 },
    { id: "data", label: "Data tier", x: 494, y: 20, w: 180, h: 300 }
  ];

  // Per-component STRIDE, the part a normal table already gets right.
  var COMPONENT_THREATS = {
    browser: ["S — a stolen session cookie is indistinguishable from the user",
              "R — the client can deny an action if only the client logs it"],
    cdn: ["T — a modified script is served to every visitor"],
    api: ["T — unvalidated input reaches the query builder",
          "E — a missing authorisation check lets one user act as another"],
    auth: ["S — token forgery if the signature is not verified",
           "I — verbose errors reveal whether an account exists"],
    db: ["I — the whole user table is one query away",
         "T — no integrity check on rows written"],
    logs: ["I — logs hold tokens and PII if not scrubbed",
           "R — an attacker who can write logs can also muddy them"]
  };

  // The system level: what an owned component REACHES, and the chains that a
  // per-component pass scores as two separate "low" findings.
  var CHAINS = [
    {
      owns: ["cdn"],
      path: ["cdn", "browser", "api", "db"],
      text: "Owning the CDN is not a 'static files' problem. Modified JS runs in " +
            "every user's browser, inside their session — so it reaches the API " +
            "with their cookie, and the API reaches the database. A per-component " +
            "table scores this 'tampering, low'."
    },
    {
      owns: ["auth"],
      path: ["auth", "db"],
      text: "The auth service holds database credentials of its own. Owning it " +
            "gives direct data-tier access WITHOUT ever passing the API's " +
            "input validation — the control everyone lists first is simply not " +
            "on this path."
    },
    {
      owns: ["api", "logs"],
      path: ["api", "logs"],
      text: "Two 'low' findings combine: the API writes tokens into logs, and " +
            "the log store has weaker access control than the DB. The token is " +
            "now readable from the softer target. Neither finding is serious " +
            "alone; together they are a credential leak."
    },
    {
      owns: ["browser"],
      path: ["browser", "api"],
      text: "A hostile client is the normal case, not an incident. Everything " +
            "past this boundary must assume the request is attacker-shaped."
    }
  ];

  var owned = Object.create(null);
  var svg = document.getElementById("dfd");
  var panel = document.getElementById("panel");
  var chainBox = document.getElementById("chains");
  var NS = "http://www.w3.org/2000/svg";

  function el(name, attrs, text) {
    var e = document.createElementNS(NS, name);
    Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (text != null) e.textContent = text;
    return e;
  }

  function node(id) {
    for (var i = 0; i < NODES.length; i++) if (NODES[i].id === id) return NODES[i];
    return null;
  }

  function activeChains() {
    return CHAINS.filter(function (c) {
      return c.owns.every(function (id) { return owned[id]; });
    });
  }

  function litEdges() {
    var lit = Object.create(null);
    activeChains().forEach(function (c) {
      for (var i = 0; i < c.path.length - 1; i++) {
        lit[c.path[i] + ">" + c.path[i + 1]] = true;
        lit[c.path[i + 1] + ">" + c.path[i]] = true;
      }
    });
    return lit;
  }

  function draw() {
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var lit = litEdges();

    ZONES.forEach(function (z) {
      svg.appendChild(el("rect", {
        x: z.x, y: z.y, width: z.w, height: z.h, rx: 10,
        class: "zone zone-" + z.id
      }));
      svg.appendChild(el("text", { x: z.x + 10, y: z.y + 20, class: "zonelabel" }, z.label));
    });

    EDGES.forEach(function (e) {
      var a = node(e.from), b = node(e.to);
      var on = lit[e.from + ">" + e.to];
      svg.appendChild(el("line", {
        x1: a.x + 55, y1: a.y + 20, x2: b.x + 55, y2: b.y + 20,
        class: "edge" + (on ? " edge-hot" : "")
      }));
      svg.appendChild(el("text", {
        x: (a.x + b.x) / 2 + 55, y: (a.y + b.y) / 2 + 14,
        class: "edgelabel" + (on ? " hot" : "")
      }, e.label));
    });

    NODES.forEach(function (nd) {
      var g = el("g", { class: "node" + (owned[nd.id] ? " owned" : ""),
                        tabindex: "0", role: "button",
                        "aria-pressed": owned[nd.id] ? "true" : "false",
                        "aria-label": nd.label + (owned[nd.id] ? ", attacker-controlled" : "") });
      g.appendChild(el("rect", { x: nd.x, y: nd.y, width: 110, height: 40, rx: 6,
                                 class: "box box-" + nd.kind }));
      g.appendChild(el("text", { x: nd.x + 55, y: nd.y + 25, class: "boxlabel" }, nd.label));
      function toggle() { owned[nd.id] = !owned[nd.id]; render(); }
      g.addEventListener("click", toggle);
      g.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); toggle(); }
      });
      svg.appendChild(g);
    });
  }

  function render() {
    draw();

    var ownedIds = NODES.filter(function (n) { return owned[n.id]; });
    panel.innerHTML = "";
    if (!ownedIds.length) {
      var p = document.createElement("p");
      p.className = "hint";
      p.textContent = "Click a component to make it attacker-controlled.";
      panel.appendChild(p);
    }
    ownedIds.forEach(function (n) {
      var h = document.createElement("h3");
      h.textContent = n.label;
      panel.appendChild(h);
      var ul = document.createElement("ul");
      (COMPONENT_THREATS[n.id] || []).forEach(function (t) {
        var li = document.createElement("li");
        li.textContent = t;
        ul.appendChild(li);
      });
      panel.appendChild(ul);
    });

    var chains = activeChains();
    chainBox.innerHTML = "";
    var ch = document.createElement("h3");
    ch.textContent = "System level — what this reaches";
    chainBox.appendChild(ch);
    if (!chains.length) {
      var q = document.createElement("p");
      q.className = "hint";
      q.textContent = ownedIds.length
        ? "No chain from this set alone. Try owning the API and the log store together."
        : "Nothing owned yet.";
      chainBox.appendChild(q);
    }
    chains.forEach(function (c) {
      var d = document.createElement("p");
      d.className = "chain";
      var strong = document.createElement("strong");
      strong.textContent = c.path.map(function (id) { return node(id).label; }).join(" → ");
      d.appendChild(strong);
      d.appendChild(document.createTextNode(" " + c.text));
      chainBox.appendChild(d);
    });
  }

  document.getElementById("reset").addEventListener("click", function () {
    owned = Object.create(null);
    render();
  });

  render();
})();

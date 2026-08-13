/* mass-assign.js — Week 10 simulation.
 *
 * WHAT THIS IS FOR
 * "The server binds the whole body" is an abstract claim until a student
 * watches their own is_admin:true field survive into the stored object. This
 * re-implements both create_user() paths from this week's real API code:
 *
 *   vulnerable_api.py:  user.update(body)                    -- everything
 *   solution_api.py:     ALLOWED_CREATE_FIELDS = {username,password}
 *                         user = {k: body[k] for k in ALLOWED_CREATE_FIELDS if k in body}
 *                         user.update({id, balance: 0, is_admin: False})
 *
 * Typed JSON is parsed for real (JSON.parse) — a syntax error is shown as
 * exactly that, not silently swallowed. Nothing is sent anywhere.
 */
(function () {
  "use strict";

  var ALLOWED = ["username", "password"];
  var SERVER_DEFAULTS = { id: "<next id>", balance: 0, is_admin: false };

  var PRESETS = [
    { label: "the attack", v: '{\n  "username": "mallory",\n  "password": "hunter2",\n  "is_admin": true,\n  "balance": 9999\n}' },
    { label: "legit signup", v: '{\n  "username": "dave",\n  "password": "correct-horse"\n}' },
    { label: "invalid JSON", v: '{ "username": "oops"' }
  ];

  var input = document.getElementById("body");
  var modeVuln = document.getElementById("mode-vuln");
  var modeFixed = document.getElementById("mode-fixed");
  var presetsEl = document.getElementById("presets");
  var errEl = document.getElementById("err");
  var resultEl = document.getElementById("result");
  var verdictEl = document.getElementById("verdict");
  var explainEl = document.getElementById("explain");

  function row(key, value, cls) {
    var div = document.createElement("div");
    div.className = "mass-assign-row " + cls;
    var k = document.createElement("span");
    k.className = "mass-assign-key";
    k.textContent = key;
    var v = document.createElement("span");
    v.className = "mass-assign-val";
    v.textContent = JSON.stringify(value);
    div.appendChild(k);
    div.appendChild(v);
    return div;
  }

  function update() {
    var raw = input.value;
    var body;
    try {
      body = JSON.parse(raw);
    } catch (e) {
      errEl.textContent = "Invalid JSON — the request never even reaches create_user(): " + e.message;
      errEl.hidden = false;
      resultEl.innerHTML = "";
      verdictEl.textContent = "";
      explainEl.textContent = "";
      return;
    }
    errEl.hidden = true;
    if (typeof body !== "object" || body === null || Array.isArray(body)) {
      errEl.textContent = "Valid JSON, but not an object — create_user() expects a JSON object body.";
      errEl.hidden = false;
      resultEl.innerHTML = "";
      return;
    }

    var fixed = modeFixed.checked;
    resultEl.innerHTML = "";

    var smuggled = [];
    var user = {};

    if (fixed) {
      // ALLOWED_CREATE_FIELDS = {"username", "password"}
      ALLOWED.forEach(function (k) {
        if (Object.prototype.hasOwnProperty.call(body, k)) {
          user[k] = body[k];
          resultEl.appendChild(row(k, body[k], "is-fromclient"));
        }
      });
      Object.keys(SERVER_DEFAULTS).forEach(function (k) {
        user[k] = SERVER_DEFAULTS[k];
        resultEl.appendChild(row(k, SERVER_DEFAULTS[k], "is-serverset"));
      });
      Object.keys(body).forEach(function (k) {
        if (ALLOWED.indexOf(k) === -1) smuggled.push(k);
      });
    } else {
      // user.update(body) -- every key the client sent lands in the stored object.
      Object.keys(body).forEach(function (k) {
        user[k] = body[k];
        var dangerous = k === "is_admin" || k === "balance" || k === "id";
        resultEl.appendChild(row(k, body[k], dangerous ? "is-smuggled" : "is-fromclient"));
      });
    }

    if (!fixed && (Object.prototype.hasOwnProperty.call(body, "is_admin") || Object.prototype.hasOwnProperty.call(body, "balance"))) {
      verdictEl.className = "verdict bad";
      verdictEl.textContent = "user.update(body) — is_admin/balance smuggled through";
      explainEl.textContent = "Nothing in create_user() distinguishes \"fields the signup form sends\" "
        + "from \"fields you typed into curl.\" Whatever key is in the JSON ends up "
        + "on the stored user, full stop.";
    } else if (fixed && smuggled.length) {
      verdictEl.className = "verdict ok";
      verdictEl.textContent = "blocked — " + smuggled.join(", ") + " never reached the model";
      explainEl.textContent = "ALLOWED_CREATE_FIELDS only pulls username/password out of the body. "
        + "id, balance and is_admin are set by the server immediately after, unconditionally — "
        + "there's no code path where a client-sent value for them survives.";
    } else if (fixed) {
      verdictEl.className = "verdict ok";
      verdictEl.textContent = "matches a legitimate signup — nothing to block";
      explainEl.textContent = "This body only sent username/password, so the allow-list and the "
        + "vulnerable path produce the same visible result here. Try adding is_admin to see them diverge.";
    } else {
      verdictEl.className = "verdict ok";
      verdictEl.textContent = "no sensitive fields in this body — nothing smuggled this time";
      explainEl.textContent = "user.update(body) still binds everything unconditionally — this "
        + "particular body just didn't include is_admin or balance. The code is identical either way.";
    }
  }

  PRESETS.forEach(function (p) {
    var b = document.createElement("button");
    b.type = "button";
    b.textContent = p.label;
    b.addEventListener("click", function () { input.value = p.v; update(); });
    presetsEl.appendChild(b);
  });

  modeVuln.addEventListener("change", update);
  modeFixed.addEventListener("change", update);
  input.addEventListener("input", update);
  input.value = PRESETS[0].v;
  update();
})();

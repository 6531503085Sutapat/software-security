/* sqli-parse.js — Week 4 simulation.
 *
 * WHAT THIS IS FOR
 * Students learn payloads and reproduce them. The thing that transfers is
 * WHY: the input stops being data and becomes syntax. So this shows the same
 * input going through two builders side by side, and colours which characters
 * the database will parse as SQL.
 *
 * The parameterised side is not "the safe version" as a slogan — the diagram
 * shows the input never entering the query text at all, which is the point
 * students have to be able to state in their own words for the Defense task.
 *
 * Everything is computed locally: no query is ever sent anywhere, and there is
 * no SQL engine here. The "parse" is a deliberately small tokeniser, honest
 * about being an illustration.
 */
(function () {
  "use strict";

  var TEMPLATE_PRE = "SELECT * FROM users WHERE name = '";
  var TEMPLATE_POST = "' AND pw = 'secret'";

  var PRESETS = [
    { label: "ordinary name", v: "alice" },
    { label: "name with an apostrophe", v: "O'Brien" },
    { label: "classic bypass", v: "' OR '1'='1" },
    { label: "comment-out", v: "admin'--" },
    { label: "UNION", v: "' UNION SELECT 1,2,3--" }
  ];

  var input = document.getElementById("inp");
  var concatBox = document.getElementById("concat");
  var paramBox = document.getElementById("param");
  var verdict = document.getElementById("verdict");
  var explain = document.getElementById("explain");
  var presets = document.getElementById("presets");

  function span(cls, text) {
    var s = document.createElement("span");
    if (cls) s.className = "tok " + cls;
    s.textContent = text;
    return s;
  }

  /* Does the supplied value escape the string literal it was pasted into?
   *
   * ANY single quote does it. The value is dropped inside `name = '…'`, so the
   * first quote in the input CLOSES that literal there and everything after it
   * is parsed as SQL.
   *
   * An earlier version of this counted quotes and asked whether the count was
   * odd. That is wrong, and wrong in the worst direction: `' OR '1'='1` has
   * four quotes, so the parity test called the classic bypass "safe" — the
   * simulation taught the opposite of the truth. Parity of the input is
   * irrelevant; position of the first quote is everything. */
  function breaksOut(v) {
    return v.indexOf("'") !== -1;
  }

  function renderConcat(v) {
    concatBox.innerHTML = "";
    concatBox.appendChild(span("tok-str", TEMPLATE_PRE));

    var escaped = breaksOut(v);
    if (!escaped) {
      concatBox.appendChild(span("tok-str", v));
      concatBox.appendChild(span("tok-str", TEMPLATE_POST));
      return false;
    }

    // Everything from the first quote onward is now parsed as SQL, not data.
    var cut = v.indexOf("'");
    if (cut > 0) concatBox.appendChild(span("tok-str", v.slice(0, cut)));
    concatBox.appendChild(span("tok-inj", v.slice(cut < 0 ? 0 : cut)));

    // A trailing comment makes the rest of the template disappear.
    if (/--|\/\*/.test(v)) {
      concatBox.appendChild(span("tok-cmt", TEMPLATE_POST));
    } else {
      concatBox.appendChild(span("tok-str", TEMPLATE_POST));
    }
    return true;
  }

  function renderParam(v) {
    paramBox.innerHTML = "";
    paramBox.appendChild(span("tok-str", "SELECT * FROM users WHERE name = "));
    paramBox.appendChild(span("tok-inj", "?"));
    paramBox.appendChild(span("tok-str", " AND pw = ?"));
    var note = document.createElement("div");
    note.style.marginTop = ".5rem";
    note.appendChild(document.createTextNode("bound separately, as data: "));
    note.appendChild(span("tok-str", JSON.stringify(v)));
    paramBox.appendChild(note);
  }

  function update() {
    var v = input.value;
    var broke = renderConcat(v);
    renderParam(v);

    verdict.className = "verdict " + (broke ? "bad" : "ok");
    verdict.textContent = broke
      ? "Concatenation: the input escaped the string literal — the database now parses it as SQL."
      : "Concatenation: this particular input stays inside the literal — but only by luck of its characters.";

    explain.innerHTML = "";
    var p1 = document.createElement("p");
    p1.textContent = broke
      ? "The orange characters are no longer a name. They are operators, "
        + "keywords and comment markers that the parser acts on. Struck-through "
        + "text is what the comment removed — including the password check."
      : "Nothing is highlighted because this value happens to contain no quote. "
        + "Try “O'Brien” — a legitimate surname breaks the same query, which is "
        + "why “reject apostrophes” is not the fix.";
    explain.appendChild(p1);

    var p2 = document.createElement("p");
    p2.textContent = "Parameterised: the query text is fixed before the value "
      + "exists. The value is sent to the database separately and can never "
      + "become syntax — so there is no payload to filter, and no clever input "
      + "to anticipate. That difference, not the payload, is what you have to "
      + "be able to explain in the Defense task.";
    explain.appendChild(p2);
  }

  PRESETS.forEach(function (p) {
    var b = document.createElement("button");
    b.type = "button";
    b.textContent = p.label;
    b.addEventListener("click", function () { input.value = p.v; update(); });
    presets.appendChild(b);
  });

  input.addEventListener("input", update);
  input.value = "' OR '1'='1";
  update();
})();

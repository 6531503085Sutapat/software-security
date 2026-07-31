/* xss-context.js — Week 5 simulation.
 *
 * WHAT THIS IS FOR
 * Students learn "escape the output" as a slogan, then escape in the wrong
 * context and believe they are done. So: ONE value lands in four sinks at
 * once, the student picks ONE escaper, and each sink is judged on its own.
 *
 * Three verdicts, not two. Calling a destroyed <script> block "SAFE" would be
 * a lie — plenty of these payloads neither execute nor leave the page intact:
 *   EXECUTES  attacker code runs
 *   BROKEN    nothing runs, but the markup or the script block is wrecked
 *   SAFE      the value stays data
 *
 * The verdicts are computed from the escaped text, not looked up in a table,
 * so a payload the lecturer types by hand is judged by the same rules. The
 * rules that matter:
 *   - a text node only cares about `<`;
 *   - an UNQUOTED attribute ends at whitespace — no `<`, no quote needed;
 *   - EVERY attribute, quoted or not, also ends at `>`, and what follows the `>`
 *     is document rather than attribute. An earlier draft judged these sinks by
 *     their attribute list alone and therefore called `Aiko><img src=x
 *     onerror=alert(1)>` SAFE: the <input> it produces really does have one
 *     ordinary `value` attribute. All of the danger was in the part that had
 *     left the tag. A sim that says SAFE over a firing payload is worse than no
 *     sim, so both attribute sinks now check what leaked past the `>`;
 *   - character references in an attribute are decoded AFTER the tokenizer has
 *     delimited it, which is why `&#34;` genuinely defuses a quote breakout —
 *     and why nothing at all defuses `javascript:`, since that value contains
 *     no character an HTML escaper touches;
 *   - inside <script> entities are NEVER decoded, and `</script>` ends the
 *     block from inside a string literal.
 *
 * Everything is local. And note what this file never does: it never hands a
 * string to the HTML parser — every insertion is textContent or replaceChildren.
 * A simulation about that mistake does not get to commit it.
 */
(function () {
  "use strict";

  /* ---------- escapers ------------------------------------------------- */

  function escHtml(v) {
    return v.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function escAttr(v) {
    return escHtml(v).replace(/"/g, "&#34;").replace(/'/g, "&#39;");
  }
  function escJs(v) {
    return v.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/'/g, "\\'")
            .replace(/\r/g, "\\r").replace(/\n/g, "\\n");
  }

  var ESCAPERS = {
    none: function (v) { return v; },
    html: escHtml,
    attr: escAttr,
    js: escJs,
    url: function (v) { return encodeURIComponent(v); }
  };

  var TAKEAWAY = {
    none: "No escaping: every sink is whatever the payload wants it to be.",
    html: "HTML-entity escaping is right for the text node and only the text node. "
        + "In an unquoted attribute there is no < to escape; in href there is nothing to escape at all; "
        + "inside <script> entities are never decoded.",
    attr: "Quoting plus entity-encoding closes both attributes — but javascript: is still a scheme, "
        + "so href needs an allowlist (http/https/mailto), not an escaper.",
    js: "Backslash escaping holds the JS string. It is not an HTML escape: it does nothing in a text node, "
      + "nothing in an unquoted attribute, and nothing against </script>.",
    url: "Percent-encoding is safe nearly everywhere and correct nearly nowhere — it destroys the text the user typed."
  };

  /* Every preset was run through a real HTML5 tokenizer before it was written
     down here. Two obvious-looking payloads did NOT do what they look like they
     do, and both are now retired:
       `" onmouseover=alert(1)`  in href="…" leaves the handler as
           onmouseover=alert(1)"  — the template's own closing quote lands in
           the handler, which is then a SyntaxError. It breaks the page instead
           of running. The quote before alert is what makes it fire.
       ` onmouseover=alert(1)`   does NOT break an unquoted attribute: the
           tokenizer skips whitespace between `=` and the value, so the value
           simply starts at `onmouseover=…`. A non-space first character is
           what makes the following space a breakout.

     Two of these are the week's own worksheet payloads, verbatim, so that what
     a student pasted into the vulnerable app in Task 1 and Task 2 is the same
     string they see judged here. `tag-close breakout` is the case the sim used
     to get wrong; it stays a preset so the fix is one click away in class. */
  var PRESETS = [
    { label: "stored XSS (Task 2)", v: "<script>alert(document.cookie)</script>" },
    { label: "img onerror (Task 1)", v: "<img src=x onerror=alert(1)>" },
    { label: "quoted-attribute breakout", v: "\" onmouseover=\"alert(1)" },
    { label: "unquoted-attribute breakout", v: "Aiko onmouseover=alert(1)" },
    { label: "tag-close breakout", v: "Aiko><img src=x onerror=alert(1)>" },
    { label: "javascript: URL", v: "javascript:alert(1)" },
    { label: "JS string breakout", v: "\";alert(document.cookie);//" }
  ];

  /* ---------- small parse helpers -------------------------------------- */

  var TAG_OPEN = /<[a-zA-Z]/;               // `<` + letter starts a tag
  var SCRIPT_TAG = /<\s*script\b/i;
  var TAG_WITH_HANDLER = /<[a-zA-Z][^>]*\son[a-z]+\s*=/i;

  /* A small HTML tag tokeniser, following the states that decide these four
     sinks: whitespace between `=` and the value is SKIPPED, a quote there opens
     a quoted value, an unquoted value ends at whitespace or `>`. Returns
     `{ attrs, end }` — the attribute list plus the index of the `>` that closed
     the tag — or null when the tag never closes (EOF inside a quoted value —
     the browser then drops the tag and eats what follows).
     Checked cell by cell against html5lib's spec tokeniser.

     `end` is not bookkeeping: it is how the sim knows the payload closed the
     tag EARLY. `<input value=Aiko><img src=x onerror=alert(1)>` parses as a
     perfectly ordinary one-attribute <input> — the danger is entirely in what
     comes after the `>`, which an attribute-only view cannot see. */
  function tagAttrs(s) {
    var i = 1, n = s.length, attrs = [];
    while (i < n && !/[\s/>]/.test(s.charAt(i))) i++;      // tag name
    while (i < n) {
      var c = s.charAt(i);
      if (/\s/.test(c) || c === "/") { i++; continue; }
      if (c === ">") return { attrs: attrs, end: i };
      var name = "";
      while (i < n && !/[\s=>]/.test(s.charAt(i))) { name += s.charAt(i); i++; }
      while (i < n && /\s/.test(s.charAt(i))) i++;
      var value = "";
      if (s.charAt(i) === "=") {
        i++;
        while (i < n && /\s/.test(s.charAt(i))) i++;       // before-value: skip ws
        var q = s.charAt(i);
        if (q === '"' || q === "'") {
          var end = s.indexOf(q, i + 1);
          if (end === -1) return null;                     // tag never closes
          value = s.slice(i + 1, end);
          i = end + 1;
        } else {
          while (i < n && !/[\s>]/.test(s.charAt(i))) { value += s.charAt(i); i++; }
        }
      }
      attrs.push({ name: name.toLowerCase(), value: value });
    }
    return null;
  }

  /* The first event-handler attribute, with its value decoded the way the parser
     decodes an attribute value. The decoding is not cosmetic: HTML-escaping
     `<img src=x onerror=alert(1)>` into an unquoted attribute really does create
     an onerror attribute — but it holds `alert(1)&gt;`, which decodes to
     `alert(1)>` and is a SyntaxError. Handler present, nothing runs. */
  function handlerOf(attrs) {
    for (var i = 0; i < attrs.length; i++) {
      if (/^on[a-z]+$/.test(attrs[i].name)) {
        return { name: attrs[i].name, value: decodeRefs(attrs[i].value) };
      }
    }
    return null;
  }

  /* Would this handler value actually run? A deliberate approximation — there is
     no eval here, and the page's CSP would not allow one. It exists because a
     payload that LOOKS like a breakout often is not, and the sim must not claim
     execution that a browser would refuse:
       `" onmouseover=alert(1)` in href="…" leaves the handler as  alert(1)"
       — the page's own closing quote lands inside it: SyntaxError.
       `<img src=x onerror=alert(1)>` HTML-escaped into an unquoted attribute
       leaves  alert(1)>  — also a SyntaxError.
     So: the value has to be nothing but call statements, end to end. Anything
     trailing (a stray quote, a stray >) means it never runs. A nested call is
     allowed one level; anything fancier is reported as NOT running, which errs
     towards under-claiming rather than crying wolf. */
  var ARG = "[^()]*(?:\\([^()]*\\)[^()]*)*";
  var CALLS = new RegExp("^(?:[A-Za-z_$][\\w$.]*\\s*\\(" + ARG + "\\)\\s*;?\\s*)+$");

  function runnableJs(v) {
    return CALLS.test(v.replace(/\/\/.*$/, "").trim());
  }

  /* Attribute values have their character references decoded AFTER the tokeniser
     has delimited them — which is why &#34; defuses a quote, and why
     `&#106;avascript:` does NOT stop being a scheme. Tabs and newlines are
     dropped from a URL before the scheme is read. */
  function decodeRefs(s) {
    var NAMED = { amp: "&", quot: '"', apos: "'", lt: "<", gt: ">", colon: ":",
                  Tab: "\t", NewLine: "\n" };
    return s
      .replace(/&#x([0-9a-fA-F]+);?/g, function (_, h) { return String.fromCharCode(parseInt(h, 16)); })
      .replace(/&#(\d+);?/g, function (_, d) { return String.fromCharCode(parseInt(d, 10)); })
      .replace(/&(amp|quot|apos|lt|gt|colon|Tab|NewLine);/g, function (_, k) { return NAMED[k]; });
  }

  function isScriptUrl(v) {
    var u = decodeRefs(v).replace(/[\t\n\r]/g, "").replace(/^\s+/, "");
    return /^javascript\s*:/i.test(u) || /^data\s*:/i.test(u);
  }

  /* First `"` that is NOT backslash-escaped, or -1. Counts the run of
     backslashes before it: an even run means the quote itself is live. */
  function liveQuote(s) {
    for (var i = 0; i < s.length; i++) {
      if (s.charAt(i) !== '"') continue;
      var n = 0, j = i - 1;
      while (j >= 0 && s.charAt(j) === "\\") { n++; j--; }
      if (n % 2 === 0) return i;
    }
    return -1;
  }

  /* What happened to the markup that escaped the tag entirely — everything past
     the `>` that closed it. A payload does not have to break OUT of an
     attribute value to be dangerous: an unquoted attribute ends at `>` just as
     it ends at whitespace, and a quoted one ends as soon as the value supplies
     the matching quote. Either way the rest of the payload is no longer an
     attribute, it is document.

     Returns "exec" when that leaked region opens a <script> or a tag whose
     event handler would really run, otherwise "broken" — because leaked markup
     is never merely "safe", the tag the page author wrote is already gone. */
  function leakVerdict(rest) {
    if (SCRIPT_TAG.test(rest)) return "exec";
    for (var i = 0; i < rest.length; i++) {
      if (!TAG_OPEN.test(rest.slice(i, i + 2))) continue;
      var t = tagAttrs(rest.slice(i));
      if (!t) continue;
      var h = handlerOf(t.attrs);
      if (h && runnableJs(h.value)) return "exec";
    }
    return "broken";
  }

  /* Quote the value the student is actually looking at, rather than a worked
     example baked into the sentence. An earlier draft hard-coded "%3Cscript%3E"
     and "&#34;" into three of these explanations, so a payload containing
     neither was described with characters that were nowhere on the screen. */
  function short(s) {
    return s.length > 46 ? s.slice(0, 46) + "…" : s;
  }
  function quoted(s) { return "“" + short(s) + "”"; }

  function V(verdict, why) { return { v: verdict, why: why }; }

  /* ---------- sink 1: HTML text node ----------------------------------- */
  /*  <p class="greet">Hello, VALUE</p>  */
  function sinkText(raw, esc, id) {
    if (TAG_OPEN.test(esc)) {
      if (SCRIPT_TAG.test(esc)) {
        return V("exec", "The browser sees < followed by a letter and builds a real <script> element, "
          + "which runs the moment the page is parsed. A text node cares about exactly one character, "
          + "and this escaper left it alone.");
      }
      if (TAG_WITH_HANDLER.test(esc)) {
        return V("exec", "The browser sees < followed by a letter and builds a real element carrying an "
          + "event handler, so the attacker's code is wired into the page and fires on the event they "
          + "chose (an image failing to load, a hover). A text node cares about exactly one character, "
          + "and this escaper left it alone.");
      }
      return V("broken", "A tag opens here, so the value is markup, not text. Nothing executes yet, "
        + "but the page structure now belongs to whoever typed this.");
    }
    if ((id === "html" || id === "attr") && /[<>&]/.test(raw)) {
      return V("safe", "&lt; is an entity: it prints as < and can never open a tag. "
        + "This is the one sink of the four where HTML-entity escaping is the right answer.");
    }
    if (id === "url" && /[<>&"']/.test(raw)) {
      return V("safe", "Percent-encoding does block it — but the greeting now reads " + quoted(esc)
        + ". Safe and wrong: the value the user typed is destroyed.");
    }
    return V("safe", "This value contains no <, so here it can only ever be text. "
      + "That is luck of the payload, not the escaper doing work.");
  }

  /* ---------- sink 2: unquoted attribute -------------------------------- */
  /*  <input value=VALUE>   (the attr escaper also adds the quotes)  */
  function sinkAttr(raw, esc, id) {
    if (id === "attr") {
      return V("safe", "The attribute is quoted and every quote inside is entity-encoded (&#34;), "
        + "so the value cannot end it. The quoting did the work; the entities keep it quoted.");
    }
    var doc = "<input value=" + esc + ">";
    var t = tagAttrs(doc);
    if (t === null) {
      return V("broken", "The quote at the front opens an attribute value that never closes, so the tag "
        + "never ends: the browser swallows the markup that follows. Nothing runs — and nothing after "
        + "this point survives either.");
    }
    var attrs = t.attrs;
    // Anything past the `>` that closed the tag is no longer an attribute.
    var leaked = t.end < doc.length - 1 ? doc.slice(t.end + 1) : "";
    var leak = leaked === "" ? null : leakVerdict(leaked);

    var h = handlerOf(attrs);
    if (h && runnableJs(h.value)) {
      return V("exec", "Whitespace ends an unquoted attribute value, so " + h.name + "= becomes a NEW "
        + "attribute on the tag. No < and no quote were needed"
        + (id === "js" ? " — and a backslash is a JS escape, meaningless to the HTML parser."
                       : " — which is why escaping angle brackets changes nothing here."));
    }
    if (leak === "exec") {
      return V("exec", "An unquoted attribute is ended by > just as surely as by a space. The > inside "
        + "this value closes the <input> early, and everything after it — " + quoted(leaked) + " — is no "
        + "longer an attribute at all. It is document, and the browser builds and runs it. "
        + "Nothing had to break out of a quote, because there was no quote.");
    }
    if (h) {
      return V("broken", "A " + h.name + " attribute IS created — but the tag's own closing characters land "
        + "inside it, so the JavaScript (" + h.value + ") is a syntax error and never runs. "
        + "The page is mangled, not owned. Payloads are shaped by their context.");
    }
    if (leak === "broken") {
      return V("broken", "The > inside this value closes the <input> early, so the rest — " + quoted(leaked)
        + " — spills out of the attribute and lands on the page as markup. Nothing executes this time, "
        + "but the tag you wrote is already gone: an unquoted attribute ends at > as well as at whitespace.");
    }
    if (attrs.length !== 1 || attrs[0].name !== "value") {
      return V("broken", "The value ends early and stray attributes appear. None of them is an event "
        + "handler, so nothing runs — but this is not the tag you wrote.");
    }
    if (id === "url") {
      return V("safe", "Percent-encoding leaves no space and no quote in the value, so it stays inside one attribute.");
    }
    if (/^\s/.test(esc)) {
      return V("safe", "The leading space is skipped by the parser, not a breakout: the value simply starts "
        + "at the first non-space character. It takes a space INSIDE the value to end it.");
    }
    return V("safe", "No quote and no whitespace inside this value, so it stays in the attribute. "
      + "Luck of the payload — quote the attribute instead of relying on it.");
  }

  /* ---------- sink 3: href="…" ------------------------------------------ */
  /*  <a href="VALUE">view profile</a>  */
  function sinkHref(raw, esc, id) {
    var tag = '<a href="' + esc + '">';
    var doc = tag + "view profile</a>";
    var t = tagAttrs(doc);
    if (t === null) {
      return V("broken", "The quotes never pair up, so the <a> tag never ends and the browser swallows "
        + "the markup that follows. Nothing runs; nothing after it survives either.");
    }
    var attrs = t.attrs;
    // The tag was meant to end at the template's own `>`, at tag.length - 1.
    var leaked = t.end < tag.length - 1 ? doc.slice(t.end + 1) : "";
    var leak = leaked === "" ? null : leakVerdict(leaked);

    var h = handlerOf(attrs);
    if (h && runnableJs(h.value)) {
      return V("exec", "The quote closes href= and " + h.name + "= lands as a new attribute on the <a>. "
        + (id === "html" ? "This escaper handled < and > and left the quote alone."
           : id === "js" ? "A backslash is not an HTML escape — the parser sees a bare quote."
           : "Nothing escaped the quote."));
    }
    if (leak === "exec") {
      return V("exec", "The quote closes href= and the > right behind it closes the whole <a> tag. What "
        + "follows — " + quoted(leaked) + " — is fresh document, and the browser runs it. Quoting is not "
        + "containment: a value that supplies its own quote AND its own > leaves the attribute entirely.");
    }
    if (h) {
      return V("broken", "A " + h.name + " attribute does appear — but the page's own closing quote lands "
        + "inside it, so that JavaScript (" + h.value + ") is a syntax error. Broken link, no execution: "
        + "to fire here the payload has to close the handler's quote itself.");
    }
    if (leak === "broken") {
      return V("broken", "The quote closes href= and the > closes the <a> tag, so the rest — "
        + quoted(leaked) + " — lands on the page as markup rather than staying in the attribute. "
        + "Nothing runs, but the link and everything the template put after it are gone.");
    }
    if (attrs.length !== 1 || attrs[0].name !== "href") {
      return V("broken", "The quote ends href= early and what follows becomes junk attribute names. "
        + "No handler, so nothing runs — the link is simply destroyed.");
    }
    if (isScriptUrl(attrs[0].value)) {
      return V("exec", "javascript: is a scheme the browser executes on click. This value contains no <, "
        + "no > and no quote, so an HTML escaper has literally nothing to escape here. "
        + "The fix is an allowlist of http/https/mailto, not an escaper.");
    }
    if (id === "url" && /^\s*(javascript|data)\s*:/i.test(raw)) {
      return V("safe", "The colon is percent-encoded (%3A), so javascript is no longer a scheme and the "
        + "browser reads a relative path. Encoding a URL still is not checking it — allowlist the scheme.");
    }
    if (/\s/.test(esc)) {
      return V("safe", "Inside quotes a space is just part of the URL, so it cannot start a new attribute here."
        + (id === "attr"
           ? " Under this escaper sink 2 is quoted too, which is exactly why it is safe as well — the quoting "
             + "is doing the work in both."
           : " Sink 2 receives the identical value into an UNQUOTED attribute, where that same space ends the "
             + "value. Same value, same escaper, different context, different outcome — compare the two panels."));
    }
    return V("safe", "No quote escapes the attribute and this is not a script scheme, "
      + "so it is only a (broken) link target.");
  }

  /* ---------- sink 4: JS string inside <script> ------------------------- */
  /*  <script>var name = "VALUE";</script>  */
  function sinkScript(raw, esc, id) {
    if (/<\/script/i.test(esc)) {
      var after = esc.slice(esc.search(/<\/script/i)).replace(/^<\/script[^>]*>?/i, "");
      if (SCRIPT_TAG.test(after) || TAG_WITH_HANDLER.test(after)) {
        return V("exec", "The </script> ends the block and what follows is a fresh tag the browser runs.");
      }
      return V("broken", "The HTML parser ends the script block at </script> — sitting inside a JS string "
        + "literal does not protect it. The code is cut in half and dies with a SyntaxError: nothing runs, "
        + "and the page's own script is gone with it."
        + (id === "js" ? " This is the hole in JS-string escaping: it escapes quotes, not </script>. "
                       + "Encode < as \\x3C as well." : ""));
    }
    var i = liveQuote(esc);
    if (i !== -1) {
      var rest = esc.slice(i + 1);
      if (/^\s*[;,+]/.test(rest)) {
        return V("exec", "The quote ends the string literal and the ; starts a new statement. "
          + (id === "html" || id === "attr"
             ? "Entities are never decoded inside <script>, so HTML escaping is invisible here."
             : "Nothing escaped the quote."));
      }
      return V("broken", "The quote ends the string, but what follows is not valid JavaScript. "
        + "SyntaxError: nothing runs and the whole block is dead.");
    }
    if (id === "js") {
      return V("safe", "Backslash escaping is exactly right for this sink: the quote is now a character "
        + "in the string, not the end of it.");
    }
    if ((id === "html" || id === "attr") && /["'<>&]/.test(raw)) {
      return V("safe", "No code runs — but the variable now literally holds " + quoted(esc)
        + ", entities and all, because the browser never decodes entities inside <script>. "
        + "Right verdict, wrong tool: nothing here was made safe on purpose.");
    }
    if (id === "url" && /["'<>&]/.test(raw)) {
      return V("safe", "Percent-encoding leaves no quote and no </script>, so nothing breaks out — "
        + "but the variable now holds " + quoted(esc) + " unless your code decodes it.");
    }
    return V("safe", "No quote and no </script> in this value, so it stays inside the string literal.");
  }

  /* ---------- rendering -------------------------------------------------- */

  /* The word is the verdict. The glyph and the colour only reinforce it \u2014 this
     is projected in a lecture hall, where the back row cannot resolve a hue and
     roughly one student in twelve cannot separate the orange from the blue. */
  var BADGE = {
    exec: "\u2716 EXECUTES",
    broken: "\u25B2 BROKEN",
    safe: "\u2714 SAFE"
  };

  /* Classes that already exist in the shared sim.css, so the three verdicts stay
     visually distinct even before this sim's own rules are added to it:
     `.verdict` is bold, `.bad` orange, `.ok` blue, plain bold for BROKEN. */
  var SHARED = { exec: "verdict bad", broken: "verdict", safe: "verdict ok" };

  var SINKS = [
    { id: 1, pre: '<p class="greet">Hello, ', post: "</p>", f: sinkText },
    { id: 2, pre: "<input value=", post: ">", f: sinkAttr },
    { id: 3, pre: '<a href="', post: '">view profile</a>', f: sinkHref },
    { id: 4, pre: '<script>var name = "', post: '";</script>', f: sinkScript }
  ];

  var input = document.getElementById("inp");
  var presets = document.getElementById("presets");
  var escaped = document.getElementById("escaped");
  var summary = document.getElementById("summary");
  var takeaway = document.getElementById("takeaway");
  var radios = document.querySelectorAll('input[name="esc"]');

  function span(cls, text) {
    var s = document.createElement("span");
    if (cls) s.className = cls;
    s.textContent = text;                 // every payload is TEXT. Always.
    return s;
  }

  function currentEscaper() {
    for (var i = 0; i < radios.length; i++) {
      if (radios[i].checked) return radios[i].value;
    }
    return "none";
  }

  function update() {
    var raw = input.value;
    var id = currentEscaper();
    var esc = ESCAPERS[id](raw);

    escaped.textContent = esc === "" ? "(empty)" : esc;
    if (esc === raw && raw !== "") {
      // "none" has not failed to find anything \u2014 it never looked. Saying so
      // matters: the whole point is that an escaper doing visible work and an
      // escaper doing the RIGHT work are different questions.
      escaped.appendChild(span("xss-context-nochange hint",
        id === "none"
          ? "  \u2190 no escaper applied: this is exactly what the user typed"
          : "  \u2190 unchanged: this escaper found nothing in THIS payload to escape"));
    }

    var counts = { exec: 0, broken: 0, safe: 0 };

    SINKS.forEach(function (sink) {
      var pre = sink.pre, post = sink.post;
      if (sink.id === 2 && id === "attr") { pre = '<input value="'; post = '">'; }

      var verdict = sink.f(raw, esc, id);
      counts[verdict.v]++;

      var code = document.getElementById("c" + sink.id);
      code.replaceChildren(
        span("xss-context-tpl", pre),
        // `tok tok-inj` is sim.css's existing "this part is the injected value"
        // highlight — it shows in all four panels at once that this is ONE value.
        span("xss-context-val tok tok-inj" + (verdict.v === "exec" ? " hot" : ""), esc),
        span("xss-context-tpl", post)
      );

      var badge = document.getElementById("b" + sink.id);
      badge.className = "xss-context-badge " + verdict.v + " " + SHARED[verdict.v];
      badge.textContent = BADGE[verdict.v];

      document.getElementById("w" + sink.id).textContent = verdict.why;
    });

    summary.textContent = counts.exec + " of 4 sinks EXECUTE"
      + (counts.broken ? "  \u00B7  " + counts.broken + " BROKEN" : "")
      + "  \u00B7  " + counts.safe + " SAFE";
    summary.className = "xss-context-sum verdict " + (counts.exec ? "hot bad" : "cool ok");
    takeaway.textContent = TAKEAWAY[id];
  }

  PRESETS.forEach(function (p) {
    var b = document.createElement("button");
    b.type = "button";
    b.textContent = p.label;
    b.addEventListener("click", function () { input.value = p.v; update(); });
    presets.appendChild(b);
  });

  input.addEventListener("input", update);
  for (var r = 0; r < radios.length; r++) {
    radios[r].addEventListener("change", update);
  }

  input.value = "<script>alert(document.cookie)</script>";
  update();
})();

/* set_form.js — the "Preview parse" button on the new/edit question-set page.
 *
 * This lived inline in set_form.html until the app-plane CSP (script-src 'self',
 * no 'unsafe-inline') made it inert. It failed silently: the button stayed on
 * the page and did nothing, which reads as a broken server rather than a blocked
 * script. Same defect class as host.html's initHost call — see the note there.
 *
 * Everything rendered goes through textContent / createElement — topic names
 * come from the (untrusted) pasted markdown, so we never touch innerHTML here.
 */
(function () {
  var btn = document.getElementById("preview-btn");
  var out = document.getElementById("preview-out");
  if (!btn || !out) return;

  function setMsg(text, isEmpty) {
    out.textContent = "";
    out.className = "preview-panel" + (isEmpty ? " empty" : "");
    out.textContent = text;
  }

  btn.addEventListener("click", function () {
    var body = new URLSearchParams();
    body.set("source_md", document.getElementById("source_md").value);
    body.set("csrf_token", document.getElementById("csrf").value);
    setMsg("Parsing…", true);
    fetch("/console/preview", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var topics = (data && data.topics) || [];
        if (!topics.length) { setMsg("No questions parsed yet — check the format.", true); return; }
        out.textContent = "";
        out.className = "preview-panel";
        var total = 0;
        topics.forEach(function (t) {
          total += t.count;
          var row = document.createElement("div");
          row.className = "pv-row";
          var name = document.createElement("span");
          name.className = "pv-t";
          name.textContent = t.topic;
          var cnt = document.createElement("span");
          cnt.className = "pv-c";
          cnt.textContent = t.count + (t.count === 1 ? " question" : " questions");
          row.appendChild(name); row.appendChild(cnt);
          out.appendChild(row);
        });
        var sum = document.createElement("div");
        sum.className = "pv-total";
        sum.textContent = topics.length + (topics.length === 1 ? " topic · " : " topics · ")
          + total + (total === 1 ? " question total" : " questions total");
        out.appendChild(sum);
      })
      .catch(function () { setMsg("Preview failed — try again.", true); });
  });
})();

/* gate-check.js — Week 15 simulation.
 *
 * WHAT THIS IS FOR
 * "Break the Build" fixes Red's menu to 3 attacks that map to a real gate and
 * 2 decoys that don't — this computes the SAME verdict security-ci.yml would,
 * for whichever findings are toggled on, rather than asserting which is which.
 *
 * Every rule/severity pair below is copied from this week's own worksheet.md
 * explanation, not invented:
 *   - outdated dependency:  Trivy fs (SCA),    HIGH   -> gate fails
 *   - Dockerfile runs root: Trivy config, DS-0002, HIGH -> gate fails
 *   - hardcoded token:      Gitleaks,          (any)  -> gate fails
 *   - chmod 777:            no Trivy rule exists at all -> nothing to gate on
 *   - FROM:latest:          Trivy config, DS-0001, MEDIUM -> detected, but
 *                            below the severity:HIGH,CRITICAL filter -> passes
 *
 * The chmod/latest pair is the actual lesson: one is invisible to the tool,
 * the other is visible but filtered by severity — same visible outcome
 * (green build), two completely different reasons.
 */
(function () {
  "use strict";

  var FINDINGS = [
    { id: "dep", label: "Outdated dependency (known CVE)", tool: "Trivy fs (SCA)",
      rule: "CVE match", severity: "HIGH", gated: true },
    { id: "root", label: "Dockerfile runs as root", tool: "Trivy config (IaC)",
      rule: "DS-0002", severity: "HIGH", gated: true },
    { id: "token", label: "Hardcoded token in source", tool: "Gitleaks",
      rule: "generic-api-key", severity: "(any match fails)", gated: true },
    { id: "chmod", label: "chmod -R 777 in Dockerfile", tool: "Trivy config (IaC)",
      rule: "no rule exists", severity: "—", gated: false, reason: "no-rule" },
    { id: "latest", label: "FROM ...:latest", tool: "Trivy config (IaC)",
      rule: "DS-0001", severity: "MEDIUM", gated: false, reason: "below-threshold" }
  ];

  var PRESETS = [
    { label: "clean PR", ids: [] },
    { label: "the 3 real Red attacks", ids: ["dep", "root", "token"] },
    { label: "just the 2 decoys", ids: ["chmod", "latest"] },
    { label: "everything", ids: FINDINGS.map(function (f) { return f.id; }) }
  ];

  var listEl = document.getElementById("findings");
  var presetsEl = document.getElementById("presets");
  var verdictEl = document.getElementById("verdict");
  var explainEl = document.getElementById("explain");

  function render() {
    listEl.innerHTML = "";
    FINDINGS.forEach(function (f) {
      var row = document.createElement("label");
      row.className = "gate-check-row";
      var cb = document.createElement("input");
      cb.type = "checkbox";
      cb.id = "f-" + f.id;
      cb.addEventListener("change", update);
      var text = document.createElement("span");
      text.className = "gate-check-text";
      var strong = document.createElement("b");
      strong.textContent = f.label;
      var meta = document.createElement("span");
      meta.className = "gate-check-meta";
      meta.textContent = f.tool + " · " + f.rule + " · severity " + f.severity;
      text.appendChild(strong);
      text.appendChild(document.createElement("br"));
      text.appendChild(meta);
      row.appendChild(cb);
      row.appendChild(text);
      listEl.appendChild(row);
    });
    update();
  }

  function update() {
    var active = FINDINGS.filter(function (f) {
      return document.getElementById("f-" + f.id).checked;
    });
    var gating = active.filter(function (f) { return f.gated; });
    var invisible = active.filter(function (f) { return f.reason === "no-rule"; });
    var filtered = active.filter(function (f) { return f.reason === "below-threshold"; });

    if (gating.length > 0) {
      verdictEl.className = "verdict bad";
      verdictEl.textContent = "build FAILS — " + gating.map(function (f) { return f.tool; }).join(", ");
      explainEl.textContent = gating.length + " of the toggled findings clear the "
        + "severity:HIGH,CRITICAL gate on their own tool. Any one of them alone is enough "
        + "to fail the build — the gate steps don't average or require a quorum.";
    } else if (active.length === 0) {
      verdictEl.className = "verdict ok";
      verdictEl.textContent = "build passes — nothing toggled";
      explainEl.textContent = "";
    } else {
      verdictEl.className = "verdict ok";
      verdictEl.textContent = "build passes — every active finding slips this gate";
      var parts = [];
      if (invisible.length) {
        parts.push(invisible.map(function (f) { return f.label; }).join(", ")
          + ": no Trivy rule exists for this pattern at all, at any severity.");
      }
      if (filtered.length) {
        parts.push(filtered.map(function (f) { return f.label; }).join(", ")
          + ": detected and reported (it's in the SARIF upload), but its severity is "
          + "below the HIGH,CRITICAL filter the gate step actually enforces.");
      }
      explainEl.textContent = parts.join(" ") + " Same green build, two different reasons — "
        + "\"the scanner didn't flag it\" and \"the scanner flagged it but the gate didn't care\" "
        + "are not the same finding when you're writing the Task 5 explanation.";
    }
  }

  PRESETS.forEach(function (p) {
    var b = document.createElement("button");
    b.type = "button";
    b.textContent = p.label;
    b.addEventListener("click", function () {
      FINDINGS.forEach(function (f) {
        document.getElementById("f-" + f.id).checked = p.ids.indexOf(f.id) !== -1;
      });
      update();
    });
    presetsEl.appendChild(b);
  });

  render();
})();

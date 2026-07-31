/* iam-evaluation.js — Cloud Infrastructure & Security, lesson 7.
 *
 * WHAT THIS IS FOR
 * Students can recite "explicit deny wins" and still not predict a single
 * request correctly, because the sentence hides three separate ways to be
 * denied and one silent way to lose an Allow. So this walks the ORDER out loud:
 *
 *   1. an explicit Deny that matches      -> DENY, evaluation stops
 *   2. else no matching Allow             -> implicit DENY
 *   3. else                               -> ALLOW
 *
 * and it names the statement that decided, every time.
 *
 * The silent case is the one worth the build: a statement whose Action and
 * Resource both match but whose Condition does not is skipped ENTIRELY. AWS
 * returns AccessDenied and never says a Condition was the reason — which is
 * exactly what a student sees when their s3:prefix rewrite "does not work".
 *
 * DELIBERATE SIMPLIFICATIONS, stated in the page too so nobody learns them
 * wrong:
 *   - the SCP is modelled Deny-only. A real SCP is also a ceiling: without an
 *     Allow (normally FullAWSAccess) everything beneath it is denied.
 *   - the permissions boundary caps only what the IDENTITY policy grants. That
 *     is the real rule for same-account access: a resource-based policy's grant
 *     is not capped by the caller's boundary. Modelling the boundary as a gate
 *     on everything would have made this simulation over-deny, and a lecturer
 *     flipping switches live would have hit it.
 *   - single account throughout: no session policies, no VPC endpoint policies,
 *     no cross-account "both sides must allow" rule.
 *
 * Everything is computed here. No network, no storage — the page is framed
 * without allow-same-origin, so it could not use either if it wanted to.
 */
(function () {
  "use strict";

  var ACCOUNT = "arn:aws:iam::111122223333:";
  var P_USER = ACCOUNT + "user/devuser";
  var P_ROLE = ACCOUNT + "role/AppRole";
  var P_ANON = "anonymous";

  var BUCKET = "arn:aws:s3:::internal-app-bucket";

  /* The label on a statement whose Condition did not hold. Named once because
     the prose in step 3 tells the student to look for this statement BY THESE
     WORDS. If the two ever drift apart the instruction points at nothing. */
  var CHIP_COND = "⚠ Condition failed — skipped";

  /* The three questions, asked in this order, WORD FOR WORD every run — including
     the runs that stop early and never really ask them. A student flipping
     switches is comparing one run against the last one, and a question that
     silently rewords itself ("Any matching Allow?" one time, "Is there a
     matching Allow?" the next) reads as a different question being asked. */
  var Q_DENY = "1 · Is there an explicit Deny that matches?";
  var Q_BOUNDARY = "2 · Does the permissions boundary allow it?";
  var Q_ALLOW = "3 · Is there a matching Allow?";

  /* ── matching ─────────────────────────────────────────────────────────── */

  /* IAM wildcards: `*` is any run of characters, `?` is exactly one. Escape
     first, then re-open the two metacharacters, so an ARN's own `.` and `$`
     stay literal. `new RegExp` is a constructor, not eval — CSP allows it. */
  function wildMatch(pattern, value) {
    var rx = "^" + pattern
      .replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
      .replace(/\\\*/g, "[\\s\\S]*")
      .replace(/\\\?/g, "[\\s\\S]") + "$";
    return new RegExp(rx).test(value);
  }

  function anyMatch(patterns, value) {
    for (var i = 0; i < patterns.length; i++) {
      if (wildMatch(patterns[i], value)) return true;
    }
    return false;
  }

  function inOffice(ip) { return ip.indexOf("10.0.") === 0; }

  /* ── condition keys ───────────────────────────────────────────────────── */
  /* `ok(req)` answers "is this Condition block satisfied?". A statement applies
     only when every one of its conditions is satisfied. */

  var COND_NO_MFA = {
    json: '"Bool": { "aws:MultiFactorAuthPresent": "false" }',
    ok: function (req) { return req.mfa === false; },
    why: function (req) {
      return req.mfa
        ? "the caller did use MFA, so aws:MultiFactorAuthPresent is \"true\", not \"false\""
        : "the caller used no MFA, so aws:MultiFactorAuthPresent is \"false\"";
    }
  };

  var COND_OFF_NETWORK = {
    json: '"NotIpAddress": { "aws:SourceIp": "10.0.0.0/16" }',
    ok: function (req) { return !inOffice(req.ip); },
    why: function (req) {
      return inOffice(req.ip)
        ? "aws:SourceIp " + req.ip + " IS inside 10.0.0.0/16, so NotIpAddress is not satisfied"
        : "aws:SourceIp " + req.ip + " is outside 10.0.0.0/16";
    }
  };

  var COND_PREFIX = {
    json: '"StringLike": { "s3:prefix": "public/*" }',
    ok: function (req) {
      return req.prefix !== "" && wildMatch("public/*", req.prefix);
    },
    why: function (req) {
      if (req.prefix === "") {
        return "this request sends no s3:prefix key at all, and StringLike on a "
          + "key that is absent never matches";
      }
      return wildMatch("public/*", req.prefix)
        ? "s3:prefix \"" + req.prefix + "\" matches \"public/*\""
        : "s3:prefix \"" + req.prefix + "\" does not match \"public/*\"";
    }
  };

  /* ── the policies ─────────────────────────────────────────────────────── */
  /* `principals` is present only on resource-based policies; an identity
     policy, an SCP and a boundary are attached TO the principal, so they carry
     no Principal element at all. */

  var POLICIES = {
    idpStar: {
      name: "AppFullAccess — the version the assistant generated",
      statements: [{
        sid: "AllowEverything", effect: "Allow",
        actions: ["*"], resources: ["*"], conditions: []
      }]
    },
    idpScoped: {
      name: "AppReadPublicOnly — the least-privilege rewrite",
      statements: [
        {
          sid: "ReadPublicObjects", effect: "Allow",
          actions: ["s3:GetObject"],
          resources: [BUCKET + "/public/*"], conditions: []
        },
        {
          sid: "ListPublicPrefix", effect: "Allow",
          actions: ["s3:ListBucket"],
          resources: [BUCKET], conditions: [COND_PREFIX]
        }
      ]
    },
    rpOpen: {
      name: "internal-app-bucket policy — the version the assistant generated",
      statements: [{
        sid: "PublicReadWrite", effect: "Allow", principals: ["*"],
        actions: ["s3:GetObject", "s3:PutObject"],
        resources: [BUCKET + "/*"], conditions: []
      }]
    },
    rpScoped: {
      name: "internal-app-bucket policy — the rewrite",
      statements: [{
        sid: "AppRoleReadPublic", effect: "Allow", principals: [P_ROLE],
        actions: ["s3:GetObject"],
        resources: [BUCKET + "/public/*"], conditions: []
      }]
    },
    scp: {
      name: "OrgGuardrails — attached to the account's OU",
      statements: [
        {
          sid: "DenyWithoutMFA", effect: "Deny",
          actions: ["s3:*"], resources: ["*"], conditions: [COND_NO_MFA]
        },
        {
          sid: "DenyOutsideOffice", effect: "Deny",
          actions: ["*"], resources: ["*"], conditions: [COND_OFF_NETWORK]
        }
      ]
    },
    boundary: {
      name: "DevBoundary — the ceiling on this user or role",
      statements: [{
        sid: "BoundaryReadOnly", effect: "Allow",
        actions: ["s3:GetObject", "s3:ListBucket"],
        resources: ["*"], conditions: []
      }]
    }
  };

  /* ── rendering the JSON ───────────────────────────────────────────────── */

  function jsonList(values) {
    if (values.length === 1) return "\"" + values[0] + "\"";
    return "[" + values.map(function (v) { return "\"" + v + "\""; }).join(", ") + "]";
  }

  function jsonPrincipal(values) {
    if (values[0] === "*") return "\"*\"";
    return "{ \"AWS\": " + jsonList(values) + " }";
  }

  function stmtJson(s) {
    var L = ["{"];
    L.push("  \"Sid\": \"" + s.sid + "\",");
    L.push("  \"Effect\": \"" + s.effect + "\",");
    if (s.principals) L.push("  \"Principal\": " + jsonPrincipal(s.principals) + ",");
    L.push("  \"Action\": " + jsonList(s.actions) + ",");
    L.push("  \"Resource\": " + jsonList(s.resources) + (s.conditions.length ? "," : ""));
    if (s.conditions.length) {
      L.push("  \"Condition\": {");
      s.conditions.forEach(function (c, i) {
        L.push("    " + c.json + (i < s.conditions.length - 1 ? "," : ""));
      });
      L.push("  }");
    }
    L.push("}");
    return L.join("\n");
  }

  /* ── analysing one statement against one request ──────────────────────── */

  function shortArn(a) {
    return a.replace("arn:aws:s3:::", "").replace(ACCOUNT, "");
  }

  function analyse(stmt, req) {
    var pr = !stmt.principals
      || stmt.principals.indexOf("*") !== -1
      || stmt.principals.indexOf(req.principal) !== -1;
    var ac = anyMatch(stmt.actions, req.action);
    var rs = anyMatch(stmt.resources, req.resource);

    var condFail = null;
    if (pr && ac && rs) {
      for (var i = 0; i < stmt.conditions.length; i++) {
        if (!stmt.conditions[i].ok(req)) { condFail = stmt.conditions[i]; break; }
      }
    }
    var applies = pr && ac && rs && !condFail;

    var why;
    if (!pr) {
      why = "Principal does not match. The statement names "
        + stmt.principals.map(shortArn).join(", ")
        + "; this caller is " + shortArn(req.principal) + ".";
    } else if (!ac) {
      why = "Action does not match. " + req.action + " is not covered by "
        + stmt.actions.join(", ") + ".";
    } else if (!rs) {
      why = "Resource does not match. " + shortArn(req.resource)
        + " is not covered by " + stmt.resources.map(shortArn).join(", ") + ".";
    } else if (condFail) {
      why = "Action and Resource both match — but the Condition does not: "
        + condFail.why(req) + ". So this statement is skipped entirely, and its "
        + stmt.effect + " never happens.";
    } else if (stmt.conditions.length) {
      why = "Matches, and its Condition holds: "
        + stmt.conditions.map(function (c) { return c.why(req); }).join("; ") + ".";
    } else {
      why = "Matches this request. It has no Condition, so nothing can narrow it.";
    }

    return { stmt: stmt, pr: pr, ac: ac, rs: rs,
             condFail: condFail, applies: applies, why: why };
  }

  /* ── which policies are even in the evaluation ────────────────────────── */

  function buildSources(req, cfg) {
    var anon = req.principal === P_ANON;
    var out = [];

    /* TWO reasons, deliberately, not one string chosen by `anon`. A source can
       be outside the evaluation for either of two unrelated reasons — the
       student switched it off, or the caller is anonymous and this kind of
       policy attaches to an identity — and the page has to say which. Folding
       them together told a student who had just UNTICKED the SCP that it did
       not apply "because this caller presented no credentials", i.e. that a
       switched-off policy was on and being bypassed. That is the exact
       misconception this screen exists to kill. */
    function src(key, label, policy, attached, offReason, anonReason) {
      var s = { key: key, label: label, name: policy ? policy.name : "",
                attached: attached, applicable: false, reason: offReason,
                analyses: [] };
      /* `!policy` is unreachable from the controls, but a typo in a preset's
         cfg would otherwise throw right here — and a throw in this IIFE leaves
         the whole page blank with nothing but a console line to say so. Degrade
         to "not attached" instead of dying. */
      if (!attached || !policy) { s.attached = false; return s; }
      if (anon && key !== "rp") { s.reason = anonReason; return s; }
      s.applicable = true;
      s.analyses = policy.statements.map(function (st) { return analyse(st, req); });
      return s;
    }

    out.push(src("idp", "Identity policy",
      cfg.idp === "star" ? POLICIES.idpStar
        : cfg.idp === "scoped" ? POLICIES.idpScoped : null,
      cfg.idp !== "none",
      "No identity policy attached in this scenario.",
      "Not in the evaluation: an anonymous caller has no IAM identity, "
        + "so no identity policy is attached to it."));

    out.push(src("rp", "Bucket policy",
      cfg.rp === "open" ? POLICIES.rpOpen
        : cfg.rp === "scoped" ? POLICIES.rpScoped : null,
      cfg.rp !== "none",
      "No bucket policy attached in this scenario.",
      ""));   /* never used: a bucket policy is the one source that still */
              /* applies to a caller with no identity at all.             */

    out.push(src("scp", "SCP", POLICIES.scp, cfg.scp,
      "No SCP switched on in this scenario.",
      "Not in the evaluation: an SCP constrains principals in your "
        + "organisation. This caller presented no credentials, so it is not one."));

    out.push(src("pb", "Boundary", POLICIES.boundary, cfg.pb,
      "No permissions boundary attached in this scenario.",
      "Not in the evaluation: a permissions boundary is attached to an "
        + "IAM user or role. This caller is neither."));

    return out;
  }

  function bySrc(sources, key) {
    for (var i = 0; i < sources.length; i++) {
      if (sources[i].key === key) return sources[i];
    }
    return null;
  }

  function cite(label, a) { return label + " → " + a.stmt.sid; }

  function citeAll(list) {
    return list.map(function (x) { return cite(x.label, x.a); }).join(" and ");
  }

  function collect(src, effect, wantApplies) {
    if (!src.applicable) return [];
    return src.analyses.filter(function (a) {
      return a.stmt.effect === effect
        && (wantApplies ? a.applies : (!a.applies && a.condFail));
    }).map(function (a) { return { label: src.label, a: a }; });
  }

  /* ── the decision ─────────────────────────────────────────────────────── */

  function decide(req, cfg) {
    var sources = buildSources(req, cfg);
    var idp = bySrc(sources, "idp");
    var rp = bySrc(sources, "rp");
    var scp = bySrc(sources, "scp");
    var pb = bySrc(sources, "pb");

    var denies = [].concat(collect(scp, "Deny", true), collect(idp, "Deny", true),
                           collect(rp, "Deny", true), collect(pb, "Deny", true));
    /* Deny statements that matched Action and Resource but whose Condition did
       not hold — step 1 names them, so a student sees WHICH guardrail lapsed
       rather than just "no Deny". Enumerated over all four sources even though
       only the SCP carries a Deny today: the line above already does, and a
       Deny added to any other policy must not silently stop being explained. */
    var nearDenies = [].concat(collect(scp, "Deny", false), collect(idp, "Deny", false),
                               collect(rp, "Deny", false), collect(pb, "Deny", false));

    var idpAllows = collect(idp, "Allow", true);
    var rpAllows = collect(rp, "Allow", true);
    var pbAllows = collect(pb, "Allow", true);
    var nearGrants = [].concat(collect(idp, "Allow", false), collect(rp, "Allow", false));

    var steps = [];
    var verdict;

    /* Step 1 — explicit Deny. */
    if (denies.length) {
      steps.push({
        state: "stop", q: Q_DENY,
        a: "Yes — " + citeAll(denies),
        d: "Evaluation stops here. An explicit Deny outranks every Allow in "
         + "every policy, and there is no order of attachment or specificity "
         + "that can undo it."
      });
      steps.push({ state: "skip", q: Q_BOUNDARY,
        a: "Not reached.", d: "The explicit Deny already ended it." });
      steps.push({ state: "skip", q: Q_ALLOW,
        a: "Not reached.", d: "Nothing here could have changed the answer." });
      verdict = {
        allow: false,
        because: "explicit Deny — " + citeAll(denies),
        sub: "This is the whole rule in one screen: two policies below can say "
           + "Allow ★ and it makes no difference."
      };
      steps.push(resultStep(verdict));
      return { sources: sources, steps: steps, verdict: verdict };
    }

    steps.push({
      state: "pass", q: Q_DENY,
      a: "No.",
      d: nearDenies.length
        ? "The Deny statements that exist were checked and skipped: "
          + nearDenies.map(function (x) {
              return cite(x.label, x.a) + ", because " + x.a.condFail.why(req);
            }).join("; ") + "."
        : "No policy in the evaluation carries a Deny that matches this "
          + "principal, action and resource."
    });

    /* Step 2 — the boundary caps the identity policy only. */
    var boundaryOk = true;
    if (!pb.applicable) {
      steps.push({
        state: "skip", q: Q_BOUNDARY,
        a: pb.reason,
        d: "A boundary is a ceiling, not a grant: it can only take privilege "
         + "away from what an identity policy hands out."
      });
    } else if (pbAllows.length) {
      steps.push({
        state: "pass", q: Q_BOUNDARY,
        a: "Yes — " + citeAll(pbAllows),
        d: "The action is inside the ceiling, so the boundary does not cap "
         + "anything the identity policy grants."
      });
    } else {
      boundaryOk = false;
      steps.push({
        state: "stop", q: Q_BOUNDARY,
        a: "No — the boundary has no matching Allow.",
        d: "So the identity policy cannot grant this, however wide it is. A "
         + "boundary holds no Deny at all: being outside it is enough."
      });
    }

    /* Step 3 — the grant. Identity-policy grants are subject to the boundary;
       a same-account bucket-policy grant is not. */
    var effective = [].concat(boundaryOk ? idpAllows : [], rpAllows);

    if (effective.length) {
      steps.push({
        state: "pass", q: Q_ALLOW,
        a: "Yes — " + citeAll(effective),
        d: "Inside one account, an Allow in EITHER the caller's identity policy "
         + "or the bucket's own policy is enough. Neither one has to know the "
         + "other exists."
         + (!boundaryOk && idpAllows.length
            ? " The identity policy's Allow was capped by the boundary, but the "
              + "bucket policy grants it directly, and a boundary does not cap "
              + "a resource-based grant."
            : "")
      });
      verdict = {
        allow: true,
        because: "granted by " + citeAll(effective),
        /* Three outcomes, because "was the boundary in play?" and "did the
           boundary permit this?" are different questions. Branching on
           pb.applicable alone printed "the boundary permitted it" directly
           underneath a step 2 that had just said "No — the boundary has no
           matching Allow": the screen contradicting itself, in the exact
           scenario the header calls out as the one a lecturer flipping
           switches live will hit. */
        sub: !boundaryOk
          ? "Read that again: the boundary did NOT permit this. The BUCKET "
            + "policy granted it, and a boundary caps only what the identity "
            + "policy hands out — never a resource-based grant. This is the "
            + "hole a permissions boundary cannot close for you."
          : pb.applicable
            ? "No Deny matched, the boundary permitted it, and an Allow matched. "
              + "All three had to be true."
            : "No Deny matched and an Allow matched. Both had to be true, and "
              + "either one flipping turns this into a denial."
      };
    } else {
      /* Three different ways to land on an implicit deny, and they are three
         different lessons. The old text used one sentence for the first two,
         which claimed "the identity policy's Allow is above the ceiling" even
         when no identity policy was attached at all — sending the student
         hunting for a statement that is not on the screen. */
      var reason;
      if (!boundaryOk && idpAllows.length) {
        reason = "The identity policy does grant this — " + citeAll(idpAllows)
          + " — and the boundary is what took it away. Nothing else grants it.";
      } else if (!boundaryOk) {
        reason = "The request is outside the boundary, and nothing grants it "
          + "either. Either one of those alone would already have denied it.";
      } else {
        reason = "Nothing grants this. AWS is deny-by-default: the ABSENCE of an "
          + "Allow is itself a denial — no statement, no message, no log line.";
      }
      if (nearGrants.length) {
        /* Point at the statement by the WORDS on its chip, never by its colour
           or its border: this is read off a projector at the back of a room,
           and the chip text is the one cue that survives that. */
        reason += " Look at the statement marked “" + CHIP_COND + "”: "
          + nearGrants.map(function (x) {
              return cite(x.label, x.a) + " matched the Action and the Resource, "
                + "but " + x.a.condFail.why(req);
            }).join("; ") + ". A failed Condition removes the statement silently "
          + "— the caller just gets AccessDenied and is never told a "
          + "Condition was the reason.";
      }
      steps.push({
        state: "stop", q: Q_ALLOW,
        a: "No — implicit DENY.", d: reason
      });
      verdict = {
        allow: false,
        /* "Capped by the boundary" only when there was something to cap. With
           no identity policy attached, the boundary removed nothing — blaming
           it there teaches a student to go read a ceiling that was never the
           reason, and hides the real one (nobody granted this at all). */
        because: (!boundaryOk && idpAllows.length)
          ? "implicit — capped by the permissions boundary"
          : "implicit — no policy grants this",
        /* The subtitle has to agree with the headline. It used to read
           "there simply is no Allow" underneath "capped by the permissions
           boundary" — two contradictory explanations of the same denial, on
           the same line, in the biggest text on the page. */
        sub: (!boundaryOk && idpAllows.length)
          ? "There IS an Allow. The boundary is a ceiling, so it removed the "
            + "privilege without any Deny being written anywhere."
          : nearGrants.length
            ? "A statement matched the Action and the Resource and still did not "
              + "apply, because its Condition did not hold."
            : "Deny-by-default. Nobody wrote a Deny; there simply is no Allow."
      };
    }

    steps.push(resultStep(verdict));
    return { sources: sources, steps: steps, verdict: verdict };
  }

  function resultStep(v) {
    return {
      state: v.allow ? "pass" : "stop",
      q: "4 · Result",
      a: v.allow ? "✓ ALLOW" : "✕ DENY",
      d: v.because.charAt(0).toUpperCase() + v.because.slice(1) + "."
    };
  }

  /* ── DOM ──────────────────────────────────────────────────────────────── */

  function el(id) { return document.getElementById(id); }

  function make(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
  }

  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

  function stmtNode(a) {
    var kind = a.applies
      ? (a.stmt.effect === "Deny" ? "is-deny" : "is-on")
      : (a.condFail ? "is-cond" : "");
    var wrap = make("div", "iam-evaluation-stmt " + kind);

    var head = make("div", "iam-evaluation-head");
    head.appendChild(make("span", null, a.stmt.sid));
    var chipText, chipCls;
    if (a.applies && a.stmt.effect === "Deny") {
      chipText = "✕ Deny applies"; chipCls = "is-deny";
    } else if (a.applies) {
      chipText = "✓ Allow applies"; chipCls = "is-on";
    } else if (a.condFail) {
      chipText = CHIP_COND; chipCls = "is-cond";
    } else {
      chipText = "— no match"; chipCls = "";
    }
    head.appendChild(make("span", "iam-evaluation-chip " + chipCls, chipText));
    wrap.appendChild(head);

    wrap.appendChild(make("div", "q iam-evaluation-json", stmtJson(a.stmt)));
    wrap.appendChild(make("p", "iam-evaluation-why", a.why));
    return wrap;
  }

  /* The policy's own name goes first, and only when it is actually attached —
     naming a policy that is switched off reads as though it were in play. */
  function renderSource(node, src) {
    clear(node);
    if (src.attached) node.appendChild(make("p", "iam-evaluation-why", src.name));
    if (!src.applicable) {
      node.appendChild(make("p", "iam-evaluation-na", src.reason));
      return;
    }
    src.analyses.forEach(function (a) { node.appendChild(stmtNode(a)); });
  }

  function renderSteps(node, steps) {
    clear(node);
    steps.forEach(function (s, i) {
      var row = make("div", "iam-evaluation-step is-" + s.state);
      row.appendChild(make("div", "iam-evaluation-num", String(i + 1)));
      var body = make("div", "iam-evaluation-body");
      body.appendChild(make("p", "iam-evaluation-q", s.q));
      body.appendChild(make("p", "iam-evaluation-a", s.a));
      body.appendChild(make("p", "iam-evaluation-d", s.d));
      row.appendChild(body);
      node.appendChild(row);
    });
  }

  /* ── presets ──────────────────────────────────────────────────────────── */

  var PRESETS = [
    {
      label: "1 · Insecure: Action ★ / Resource ★",
      cfg: { principal: P_USER, action: "s3:DeleteObject",
             resource: BUCKET + "/secret/keys.txt", ip: "10.0.5.9", mfa: true,
             prefix: "", idp: "star", rp: "none", scp: false, pb: false },
      nudge: "Try: tick the permissions boundary. The same ★ policy stops "
           + "being able to delete anything — a ceiling needs no Deny."
    },
    {
      label: "2 · The least-privilege rewrite",
      cfg: { principal: P_USER, action: "s3:GetObject",
             resource: BUCKET + "/public/report.pdf", ip: "10.0.5.9", mfa: true,
             prefix: "", idp: "scoped", rp: "none", scp: false, pb: false },
      nudge: "Legitimate work still works. Try: switch the resource to "
           + "secret/keys.txt — same caller, same policy, implicit DENY."
    },
    {
      label: "3 · A Condition fails, so the Allow does not apply",
      cfg: { principal: P_USER, action: "s3:ListBucket", resource: BUCKET,
             ip: "10.0.5.9", mfa: true, prefix: "secret/",
             idp: "scoped", rp: "none", scp: false, pb: false },
      nudge: "Try: set s3:prefix to public/ and it flips to ALLOW. AWS never "
           + "tells you a Condition was the reason — you only see AccessDenied."
    },
    {
      label: "4 · Principal ★ on the bucket + an anonymous caller",
      cfg: { principal: P_ANON, action: "s3:PutObject",
             resource: BUCKET + "/secret/keys.txt", ip: "203.0.113.42",
             mfa: false, prefix: "", idp: "scoped", rp: "open",
             scp: true, pb: true },
      nudge: "This is lesson 7's bug. The SCP and the boundary are both ON and "
           + "neither fires: they constrain identities, and this caller has none."
    },
    {
      label: "5 · Explicit Deny beats everything",
      cfg: { principal: P_USER, action: "s3:GetObject",
             resource: BUCKET + "/public/report.pdf", ip: "203.0.113.42",
             mfa: false, prefix: "", idp: "star", rp: "open",
             scp: true, pb: false },
      nudge: "Two policies say Allow ★; one SCP Deny outranks both. Try: "
           + "office IP and MFA on — both Denies lapse and it becomes ALLOW."
    }
  ];

  /* ── wiring ───────────────────────────────────────────────────────────── */

  var FIELDS = ["f-principal", "f-action", "f-resource", "f-ip", "f-prefix",
                "f-mfa", "f-scp", "f-pb"];

  function radioValue(name) {
    var list = document.getElementsByName(name);
    for (var i = 0; i < list.length; i++) if (list[i].checked) return list[i].value;
    return "none";
  }

  function readCfg() {
    return {
      principal: el("f-principal").value,
      action: el("f-action").value,
      resource: el("f-resource").value,
      ip: el("f-ip").value,
      prefix: el("f-prefix").value,
      mfa: el("f-mfa").checked,
      idp: radioValue("idp"),
      rp: radioValue("rp"),
      scp: el("f-scp").checked,
      pb: el("f-pb").checked
    };
  }

  function applyCfg(c) {
    el("f-principal").value = c.principal;
    el("f-action").value = c.action;
    el("f-resource").value = c.resource;
    el("f-ip").value = c.ip;
    el("f-prefix").value = c.prefix;
    el("f-mfa").checked = c.mfa;
    el("f-scp").checked = c.scp;
    el("f-pb").checked = c.pb;
    el("idp-" + c.idp).checked = true;
    el("rp-" + c.rp).checked = true;
  }

  function update() {
    var cfg = readCfg();
    var req = { principal: cfg.principal, action: cfg.action,
                resource: cfg.resource, ip: cfg.ip, mfa: cfg.mfa,
                prefix: cfg.prefix };
    var r = decide(req, cfg);

    renderSource(el("src-idp"), bySrc(r.sources, "idp"));
    renderSource(el("src-rp"), bySrc(r.sources, "rp"));
    renderSource(el("src-scp"), bySrc(r.sources, "scp"));
    renderSource(el("src-pb"), bySrc(r.sources, "pb"));
    renderSteps(el("steps"), r.steps);

    el("verdict").className = "iam-evaluation-verdict "
      + (r.verdict.allow ? "is-allow" : "is-deny");
    el("badge").textContent = r.verdict.allow ? "✓ ALLOW" : "✕ DENY";
    el("because").textContent = r.verdict.because;
    el("sub").textContent = r.verdict.sub;
  }

  function onManualChange() {
    el("nudge").textContent = "";
    update();
  }

  PRESETS.forEach(function (p) {
    var b = make("button", null, p.label);
    b.type = "button";
    b.addEventListener("click", function () {
      applyCfg(p.cfg);
      update();
      el("nudge").textContent = p.nudge;
    });
    el("presets").appendChild(b);
  });

  FIELDS.forEach(function (id) {
    el(id).addEventListener("change", onManualChange);
  });
  ["idp", "rp"].forEach(function (name) {
    var list = document.getElementsByName(name);
    for (var i = 0; i < list.length; i++) {
      list[i].addEventListener("change", onManualChange);
    }
  });

  applyCfg(PRESETS[0].cfg);
  update();
  el("nudge").textContent = PRESETS[0].nudge;
})();

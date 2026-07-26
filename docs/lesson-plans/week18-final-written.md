# Lesson Plan — Week 18: Final, Written Exam

| | |
|---|---|
| **Course** | Software Security (⬚ course code) |
| **Week / date** | 18 · ⬚ |
| **Contact time** | 150 min — a single written-exam block. No lecture, no lab (`AGENDA.md` per-week table row 18, and *Week 8 / 18 — Written exam*: "120 min (midterm) / 150 min (final)") |
| **Lab folder** | `labs/week18-final-written` (holds the paper, not a target) |
| **Slides** | `slides/week18.md` — proctor deck, not a teaching deck |
| **Covers** | Cumulative, emphasis on **Weeks 10–16** (API, memory safety, supply chain, cloud/container, AI/LLM, DevSecOps) |
| **Standards** | The ids `course-plan-19weeks.md` attaches to the emphasised weeks: **OWASP API Security Top 10** (W10) · CISA/ONCD memory-safety roadmaps (W11 — the course plan attaches no OWASP id to that week) · **A03:2025** and **A08:2025** (W12) · **A02:2025** (W13) · **OWASP Top 10 for LLM Apps (2025)**, LLM01 prompt injection (W14) · **A09** and **A10** (W15). The paper's own instruction line asks students to map findings to OWASP 2025 / API / LLM Top 10 / CWE; Section B requires the student to supply the id. |
| **CLOs addressed** | **CLO1** model · **CLO2** exploit · **CLO3** remediate · **CLO4** tooling · **CLO5** evaluate & communicate (course specification §6, row 18 — note this row assigns CLO**5**, not CLO6, unlike the Week 8 row) |

> **This plan quotes no exam question, no answer and no flag.** The Form A paper is public
> (`labs/week18-final-written/exam.md`); the keys, Form B and the item bank are instructor-only
> and are referenced here by path only.

---

## 1. What this paper evidences

This is an assessment week, so the objectives are stated as *what a script demonstrates about its
author*, not as what is taught. A student whose script scores well has shown that they can:

**Knowledge (K)**
- K1 — Recall and restate, unaided, the modern-stack concepts of Weeks 10–16 (Section A, 30 pts).
- K2 — Classify a given flaw against the taxonomies the paper names — OWASP 2025, the API Top 10,
  the LLM Top 10, CWE — rather than describing it loosely (Section B asks for the id as well as
  the flaw).
- K3 — State how the supply-chain integrity controls fit together (SBOM, SLSA, artifact signing
  with Cosign), what least privilege means in cloud/IAM, and what a DevSecOps gate is for — the
  topics the proctor deck lists under *What's assessed* (`slides/week18.md`).

**Skills (P)**
- P1 — Read a short code snippet cold and identify the flaw, its OWASP/CWE id and its fix
  (Section B, 20 pts).
- P2 — Work an applied problem *on paper*, with no running target and no tooling to hand: give the
  steps and the named tools for a pipeline task, and design the control that removes a stated flaw
  (Section C, 30 pts).
- P3 — Produce an extended design answer that says **where a control belongs in the pipeline**, not
  only what it is called, as prose an engineer could act on (Section D, 20 pts; the deck's *Tips*
  slide makes this the paper's stated score-saver).

**Attitude (A)**
- A1 — Answer in their own words. **Note:** unlike the Week 8 paper, this paper carries no "answer
  in your own words" instruction line. If that is the marking stance — and §7 assumes it is — it
  has to be said aloud (§4), because the script does not say it.
- A2 — Carry the rules of engagement into a written scenario ([ETHICS.md](../../ETHICS.md)).
  Likewise **not** stated on this paper; the Week 8 paper has such a line and this one does not.
- A3 — Sit an individual assessment under the integrity conditions in §6, and be able to stand
  behind the script as their own work.

## 2. Exam blueprint — what is assessed

Taken from the paper itself (`labs/week18-final-written/exam.md`): **150 min · 100 pts**. Kept at
section granularity so this file can stay public.

| Section | Marks | Shape | Weeks drawn on | CLOs |
|---|---|---|---|---|
| **A — Modern-stack concepts** | 30 (6 × 5) | Short answer | 10–15 | CLO1, CLO4 |
| **B — Spot the Vulnerability** | 20 (4 × 5) | Name the flaw + OWASP/CWE + the fix, from a code snippet | 10–14 | CLO2, CLO3 |
| **C — Applied** | 30 (3 × 10) | Multi-part applied reasoning across the emphasised weeks | 10–14 | CLO3, CLO4 |
| **D — Design & DevSecOps** | 20 (2 × 10) | Extended written answer | 12–15 | CLO1, CLO5 |

The **per-section CLO attribution above is this plan's reading**, not the repository's: the course
specification assigns CLOs at *week* granularity (§6 row 18 → CLO1–CLO5) and nowhere maps them to
sections. The *Weeks drawn on* column describes **Form A**; see §5 for how Form B differs.

**Read the coverage honestly before you claim it in a programme review.**

- **CLO4 is genuinely carried here**, which it was not on the midterm. Section C asks for named
  tools and an ordered set of pipeline steps and Section D asks for scanner-and-gate design, so
  tooling is worth far more than the single 5-pt item it was worth in Week 8.
- **CLO2 is evidenced only as recognition and mechanism explanation.** There is no running target
  and no interpreter; a student cannot demonstrate exploitation on this paper. The exploitation
  half of the final component is Week 19 (`labs/week19-final-ctf-capstone/ctf.md`).
- **CLO5 is half-evidenced.** The *communicate a finding, its impact and its fix* half is carried
  by the extended prose in Sections C and D. The *evaluate security work produced by others,
  including AI-generated code and advice* half (course specification §3) is **not** on this paper —
  it is carried by the weekly worksheets' *Audit the AI* part and by the Week 19 graded demos.
- **CLO6 is not claimed**, and consistently so: course specification §6 row 18 does not assign it,
  and the paper carries no ethics instruction line. Integrity here is procedural (§6), not a marked
  item.

**Scope: settle "cumulative" before the cohort revises.** The paper is labelled cumulative, but its
blueprint draws on Weeks 10–16 throughout, and `instructor/exams/item-bank.md` sources it from the
**FINAL POOL (Weeks 10–16)**. A student who revises only the second half is not materially exposed.
`labs/week18-final-written/README.md` says as much in its own *Scope assumption* note — it leaves
cumulative-versus-second-half-only as an **open instructor decision**. Resolve it at the Week 17
debrief, because it determines what the cohort revises and how honestly the word "cumulative" can
be used in a programme report. While settling the wording, note that "Weeks 10–16" sends students
to revise Week 16, which is the Capstone Studio — `course-plan-19weeks.md` gives it no
**Concept:** bullet (unlike Weeks 10–15) and `labs/week16-capstone/README.md`'s Practice CTF
draws on "Weeks 1–15", not new Week 16 material — so the examinable band is effectively
Weeks 10–15.

## 3. Preparation before the day

- **Students, before the exam:** study cumulatively with emphasis on Weeks 10–16
  (`labs/week18-final-written/README.md` step 1), using the Week 17 consolidation — the cumulative
  review quiz `quizzes/quiz2.md`, *Security Jeopardy: Champions Edition*, and the mock final CTF
  `labs/week17-review-final-prep/mock-ctf.md`, which is run in the exact format of Week 19.
- **The permissible-aid gap — check this first.** `instructor/anti-cheating.md` §C names a
  **one-page cheat sheet** as the only documented permissible aid for the written exams (W8/W18).
  That cheat sheet is a **Week 7** deliverable (`labs/week07-review-midterm-prep/README.md`;
  `course-plan-19weeks.md` Week 7 section) and it covers **Weeks 1–6**. `labs/week17-review-final-prep/README.md`
  asks for **no** equivalent deliverable. So if the final is run open-note, the only cheat sheet the
  course has ever asked students to produce covers the wrong half of the syllabus. Decide open/closed
  at the Week 17 debrief and, if open-note, add the deliverable to Week 17 first.
- **Instructor, at the Week 17 debrief** (`AGENDA.md`, Week 7 & 17 review block, 4:30–5:00
  *Debrief: common mistakes + exam logistics*): announce the open/closed-note decision, resolve the
  scope assumption above, and state which form of the paper is being sat.
- **Instructor, before the day:** confirm the exam version — the proctor deck's own note is to
  rotate from the final pool of `instructor/exams/item-bank.md` each cohort. Produce the printed
  papers from the chosen form and check the code blocks survived printing (§11). Have the matching
  key to hand and only that key.
- **⬚** Room, seating plan, number of sections/sittings, invigilator roster, script paper and
  printing arrangements are not recorded in this repository.

## 4. The 150-minute block — logistics

`AGENDA.md` budgets **150 min** for the final written block and nothing else; it does not budget
briefing or settling time, so the pre-clock allowance is **⬚** and must come from the faculty's own
exam regulations. Order of business follows the proctor deck `slides/week18.md`:

| Step | Action | Source |
|---|---|---|
| Before the clock | Confirm the exam version aloud; state the duration, the open/closed-note rule and the integrity policy (no AI, no phones) | `slides/week18.md` title-slide presenter note |
| Before the clock | State the format: cumulative, weighted toward the modern-stack half; sections mirror the midterm — concepts / spot-the-vuln / applied / design, 100 pts | `slides/week18.md`, slide *Format* and its note |
| Before the clock | Show *What's assessed* briefly — supply-chain integrity (SLSA / SBOM / Cosign), cloud and IAM least privilege, LLM and agentic threat modelling, DevSecOps gate design, spot-the-vuln / design-the-fix across the term, memory-safe-language and Secure-by-Design tradeoffs. The deck's own instruction: exam day, **don't teach** | `slides/week18.md`, slide *What's assessed* |
| Before the clock | State the score-saver: reason about design rather than single bugs; always name the mitigation **and where it belongs in the pipeline**; map to OWASP 2025 / LLM Top 10 / CWE. Say it once, then start | `slides/week18.md`, slide *Tips* and its note |
| Before the clock | State the materials rule explicitly — **the paper does not state it** (see below) | This plan; `exam.md` header carries no closed-book line |
| Clock starts | 150 min writing. Keep talking minimal once the clock runs | `AGENDA.md`; `slides/week18.md` presenter note |
| On the paper | Name, Student ID and Date fields are on the paper — check they are filled before collecting | `exam.md` header |
| At collection | Collect papers; remind the cohort that Week 19 is the team capstone CTF **plus graded project demos**, and that they must bring a runnable project with threat model, vuln report, SBOM, signed artifact and CI pipeline | `slides/week18.md` closing note; `labs/week19-final-ctf-capstone/README.md`, *Bring* |

**Materials allowed.** The Week 8 paper states "Closed book unless stated otherwise" in its header.
**This paper states nothing**: `labs/week18-final-written/exam.md` carries no materials line, the
week README is silent, and `slides/week18.md` slide *Format* leaves open-note as "(set by
instructor)". The only documented permissible aid anywhere in the repository is the one-page cheat
sheet in `instructor/anti-cheating.md` §C — see the gap flagged in §3. The decision itself is **⬚**;
record it here once made, write it on the board, and say it aloud, because a student who has sat
the Week 8 paper will otherwise assume the Week 8 rule.

## 5. Forms A and B, sections, and make-up sittings

The course specification §9 states the arrangement: *exams exist in two parallel forms (A/B) drawn
from a maintained item bank, supporting make-up sittings and reducing answer sharing.*

| Form | Where it lives | Status | Use |
|---|---|---|---|
| **A** | `labs/week18-final-written/exam.md` | **Public** — in the student-facing repo | The default sitting, *if* the cohort has not seen it |
| **B** | `instructor/exams/week18-final-written-formB.md` | Instructor-only (git-ignored) | Pre-assembled parallel form, same section weights as Form A; drawn from the FINAL POOL of `instructor/exams/item-bank.md` |

- Form B is built to the **same section weights and the same 150 min / 100 pts** as Form A, so a
  Form B sitting needs no scaling. It matches on weights and duration only — it distributes topics
  differently across its sections, so the *Weeks drawn on* column in §2 does **not** describe Form B.
- **Running both forms in the same term needs a hand-edit first.** Form B's own header records that
  its Sections A, C and D are cleanly differentiated from Form A, but that **two of its Section B
  code snippets are close in topic to two of Form A's**, and that those two should be varied
  further in wording before both forms are sat in the same term — which is exactly the case when a
  cohort is split across two sections. Do that edit before printing, not after the first sitting.
- Once Form B is deployed it becomes as public as Form A and must itself be rotated next cohort;
  `instructor/exams/item-bank.md` records that the public exam files are static and leak between
  cohorts.
- **Make-up sittings:** run the form the main cohort did *not* sit. Which form the main sitting used
  therefore has to be recorded on the day.
- **⬚** Make-up sitting date, eligibility rules and any cap on the make-up mark are institutional
  and not recorded in this repository.

## 6. Invigilation and academic integrity

Sourced from `instructor/anti-cheating.md` §C (*Written exams (W8/W18)*) and the `slides/week18.md`
presenter notes. Do **not** import the Google Form checklist from §C — that is scoped to the online
weekly quizzes, not to this paper.

- In-class and **monitored** throughout.
- **Multiple versions / shuffled sections** where the room allows it, and closed book — or the
  one-page cheat sheet only (but read §3 before relying on that aid existing).
- **No phones, no AI**, stated aloud before the clock starts.
- The paper is individual work. Because this paper carries no "own words" instruction line (§1, A1),
  say it aloud — the marking stance in §7 depends on it.
- Identical wrong answers across adjacent scripts are the written-exam form of the red flag listed
  in `instructor/anti-cheating.md` §F. Keep the seating record so an adjacency claim can be checked
  later.
- **If copying is found:** follow `instructor/anti-cheating.md` §G — keep the evidence, apply the
  syllabus penalty consistently, and follow [ETHICS.md](../../ETHICS.md) plus **⬚** (institutional
  conduct process, as flagged in the course specification §11).

## 7. Marking

- **Who marks: ⬚.** The course specification names one instructor and records no TA, second-marker
  or moderation arrangement. If more than one person marks, fix a section split (one marker takes
  Section D across all scripts) so that a judgement call is at least applied consistently.
- **The key.** `instructor/exams/week18-final-written-answers.md` for Form A;
  `instructor/exams/week18-final-written-formB-answers.md` for Form B. Each carries the per-section
  mark split and its own marking notes, and both state that partial credit is available for correct
  reasoning. Match the key to the deployed form before the first script — the two papers share
  section titles, weights and duration, which is exactly what makes a mismatched key easy to miss.
- **Borderline answers.** The course specification §8 sets the course-wide stance: partial credit is
  available for a correct mechanism explained without a working exploit. On this paper the two
  classes that will recur are:
  1. a Section B answer that names the mechanism and gives a workable fix but omits or misnames the
     OWASP/CWE id;
  2. a Section C or D answer that names the right control but never says **where in the pipeline it
     belongs** — which the deck's *Tips* slide told students was the thing being rewarded, so this
     is a deliberate discrimination point, not an oversight to be waived.

  Decide each such class **once**, write the ruling in the margin of your working copy of the key,
  apply it to every script, and then carry the ruling into §8 as a candidate item-bank note.
- **Score entry.** Enter the mark against **Final** in the gradebook; `instructor/GRADEBOOK.md`
  computes **Final % = average of W18 and W19**, so this paper is half of the 25% final component
  (course specification §4).
- **⬚** Grading scale / letter-grade boundaries (institutional).

## 8. After the exam — item analysis and the item bank

The repository defines the *loop* but not the *statistics*. Everything below that is not sourced is
marked ⬚ rather than guessed.

1. **Mark, then look at the paper rather than the students.** For each item, note where the cohort
   clustered: near-universal correct (the item discriminated nothing), near-universal wrong (the
   item was mis-set, mis-worded, or the teaching week did not land), and split-with-good-students-
   wrong (the item is probably ambiguous).
2. **Separate a bad item from a real gap.** This is the last written instrument of the term, so a
   cohort-wide failure cannot be retaught to this cohort. It is a signal about the emphasised
   teaching week (10–16) and about Week 17's consolidation — record it against that week, not
   against the item.
3. **The one same-term use of the analysis.** If marking finishes before Week 19, a topic the cohort
   failed cohort-wide is a fair subject for the unscripted questions in the Week 19 graded demos
   (`instructor/anti-cheating.md` §D provides for 1–2 unscripted questions per team). Optional, and
   it probes rather than re-teaches.
4. **Replace, don't patch.** Items are rotated from the FINAL POOL of
   `instructor/exams/item-bank.md`, which exists for exactly this — the file states its purpose as
   rotating and rebuilding the written exams each cohort because the public exam files leak.
   `instructor/anti-cheating.md` §E requires rotating the question bank every cohort regardless of
   how the items performed.
5. **Write the ruling back.** Every borderline-answer ruling made in §7 is evidence that an item is
   ambiguous. Add it to the item's marking note in the bank, or reword the item, before it is used
   again. While you are there, deal with the Section B overlap noted in §5 — it is a bank-depth
   problem, not a wording problem, and the fix is more Section B snippets in the FINAL POOL.
6. **Close the loop on the forms.** Record which form this cohort sat, so the next cohort's Form A
   is not the paper this cohort has photographed.

**⬚ Not defined anywhere in this repository, and deliberately not invented here:** which item
statistic is used (facility index, discrimination index, point-biserial or none), the threshold at
which an item counts as discriminating poorly, who reviews the analysis, when it is done, and where
it is recorded. Fix these once and add them to `instructor/exams/item-bank.md`, not to this public
file.

## 9. Assessment for this week

| Instrument | Evidence | Outcome | Weight |
|---|---|---|---|
| Final written paper, Sections A–D | The script, 100 pts | K1–K3, P1–P3, A1–A3 | Half of the 25% final component (`instructor/GRADEBOOK.md`: Final % = average of W18, W19) |
| Invigilation record + seating record | Sitting conditions, form sat, incidents | A3 | Integrity control, not a mark |
| Item analysis (§8) | Per-item performance | Course-level, not student-level | Feeds the FINAL POOL and next cohort's Week 17 |

No worksheet, no weekly quiz and no flag this week — nothing is submitted to Classroom or GitHub.

## 10. Materials

- Paper, Form A (public): `labs/week18-final-written/exam.md`
- Week brief: `labs/week18-final-written/README.md`
- Proctor deck: `slides/week18.md` (Marp)
- Instructor-only, **never published**: `instructor/exams/week18-final-written-answers.md`,
  `instructor/exams/week18-final-written-formB.md`,
  `instructor/exams/week18-final-written-formB-answers.md`,
  `instructor/exams/item-bank.md`, `instructor/anti-cheating.md`, `instructor/GRADEBOOK.md`
- What students revised from: `labs/week17-review-final-prep/` (`mock-ctf.md`), `quizzes/quiz2.md`,
  and the Week 10–16 lab folders
- What comes next: `labs/week19-final-ctf-capstone/` (`ctf.md`, README *Bring* list),
  [project/README.md](../../project/README.md)
- Rules of engagement: [ETHICS.md](../../ETHICS.md)
- **⬚** Printed papers, script booklets, room booking

## 11. Risks and contingencies

| Risk | Mitigation |
|---|---|
| **Form A is published in the public repo** and, as `instructor/exams/item-bank.md` states, the public exam files are static and leak between cohorts — a repeating student or a shared drive from last year has the paper | Decide Form A vs Form B *before* the sitting; if there is any chance the cohort holds the paper, deploy Form B or rebuild Form A's items from the FINAL POOL (`instructor/anti-cheating.md` §E) |
| **The cohort is split across sections and both forms are sat in the same term** — Form B's header records that two of its Section B snippets are topically close to Form A's | Hand-vary those two snippets' wording *before printing*, as the Form B header instructs. Sections A, C and D need no such edit |
| **The paper states no materials rule** — unlike the Week 8 paper, `exam.md` carries no closed-book line, so a cohort that sat Week 8 will assume the Week 8 rule | Decide at the Week 17 debrief, state it aloud before the clock, write it on the board, and add the line to the paper before it is used again |
| **Open-note is chosen but no aid exists for the right half of the course** — the one-page cheat sheet is a Week 7 deliverable covering Weeks 1–6; Week 17 asks for no equivalent | Decide open/closed *before* Week 17 and, if open-note, add the cheat-sheet deliverable to `labs/week17-review-final-prep/README.md` so students produce one covering Weeks 10–16 |
| A Form B sitting marked against Form A's key — the two share section titles, weights and duration, so the mismatch is not obvious until the marks look strange | Write the form letter on the board and on the script header; open only the deployed form's key while marking |
| `instructor/` is git-ignored — a colleague marking from a fresh clone of the public repo has **no key at all**, and no Form B | Transfer the key out-of-band before marking day; never "fix" this by committing the key |
| Printing a Markdown paper: Section B is a set of fenced code blocks in several languages, and later sections cross-reference them. A wrapped or page-broken snippet changes what a "spot the vuln" item actually shows, and a snippet printed on a different page from the item that refers back to it is worse | Export to PDF once, read the printed proof line by line, confirm no snippet wraps or splits across a page, and check that each cross-referenced snippet is visible from the item that cites it, before duplicating |
| The README's *Scope assumption* is left unresolved, so half the cohort revises Weeks 10–16 only and half revises all nineteen weeks | Announce the scope decision at the Week 17 debrief, in the same slot as the form and materials decisions |
| No lab block this week, so nothing is checked on a machine — Week 19 is a 240-min team CTF **plus graded demos**, and the first time a team discovers their project will not build is at its start | Use the deck's closing note at collection: state the Week 19 *Bring* list (threat model, vuln report, fixed code, SBOM, signed artifact, CI pipeline) and tell teams to do a dry run before they leave |
| A student misses the sitting | Run the other form (§5); eligibility and date are **⬚** (institutional) |
| Multiple sections / multiple sittings of the same cohort | The later sitting must not sit the same form as the earlier one; record which form each section sat, and apply the Section B hand-edit above. Section and seating arrangements are **⬚** |

## 12. Post-teaching reflection

*Complete after the session — this also feeds the course's engagement data.*

- Attendance / completion: ⬚
- Form sat (A / B), and by which section: ⬚
- Materials rule actually applied (closed book / one-page cheat sheet), and whether it was announced in time: ⬚
- Time actually used by the cohort (did anyone need the full 150 min?): ⬚
- Section-by-section mark distribution, and which section was weakest: ⬚
- Items that discriminated poorly, and what replaced them in the FINAL POOL: ⬚
- Borderline-answer rulings made during marking, and the item wording they imply: ⬚
- Integrity incidents, and how they were handled: ⬚
- Anything to change before this exam runs again: ⬚

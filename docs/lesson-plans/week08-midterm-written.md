# Lesson Plan — Week 8: Midterm, Written Exam

| | |
|---|---|
| **Course** | Software Security (⬚ course code) |
| **Week / date** | 8 · ⬚ |
| **Contact time** | 120 min — a single written-exam block. No lecture, no lab (`AGENDA.md`, *Week 8 / 18 — Written exam*) |
| **Lab folder** | `labs/week08-midterm-written` (holds the paper, not a target) |
| **Slides** | `slides/week08.md` — proctor deck, not a teaching deck |
| **Covers** | Weeks 1–6 |
| **Standards** | The OWASP 2025 ids the course plan attaches to the covered weeks: **A04** (W3 crypto), **A05** (W4 injection), **A01 / A07** (W6 authn/access). Section B of the paper requires students to supply CWE ids; none are named in this plan. |
| **CLOs addressed** | **CLO1** model · **CLO2** exploit · **CLO3** remediate · **CLO4** tooling · **CLO6** evidence & ethics (course specification §6, row 8) |

> **This plan quotes no exam question, no answer and no flag.** The Form A paper is public
> (`labs/week08-midterm-written/exam.md`); the keys, Form B and the item bank are instructor-only
> and are referenced here by path only.

---

## 1. What this paper evidences

This is an assessment week, so the objectives are stated as *what a script demonstrates about its
author*, not as what is taught. A student whose script scores well has shown that they can:

**Knowledge (K)**
- K1 — Recall and restate, unaided, the foundational concepts of Weeks 1–3 (Section A, 30 pts).
- K2 — Classify a given vulnerability against the CWE / OWASP taxonomy rather than describing it
  loosely (Section B requires the vulnerability *and* its CWE).
- K3 — State the secure-design principles the course names — "least privilege, defense in depth,
  fail closed" (`labs/week08-midterm-written/README.md`, *Format*; the repo's own spelling).

**Skills (P)**
- P1 — Read a short code snippet cold and identify the flaw, its CWE and its fix (Section B, 20 pts).
- P2 — Reason about SQL injection *on paper*, with no running target and no interpreter to test
  against: construct injections for a stated query and justify each token (Section C, 30 pts).
- P3 — Produce a defence and a secure design as prose an engineer could act on, not a list of
  keywords (Section D, 20 pts).

**Attitude (A)**
- A1 — Answer in their own words, as the paper's own instruction line requires.
- A2 — Carry the rules of engagement into a written scenario: the paper states that sandbox and
  ethics rules apply to all scenarios ([ETHICS.md](../../ETHICS.md)).
- A3 — Sit an individual assessment under the integrity conditions in §6, and be able to stand
  behind the script as their own work.

## 2. Exam blueprint — what is assessed

Taken from the paper itself (`labs/week08-midterm-written/exam.md`): **120 min · 100 pts · closed
book unless stated otherwise**. Kept at section granularity so this file can stay public.

| Section | Marks | Shape | Weeks drawn on | CLOs |
|---|---|---|---|---|
| **A — Concepts** | 30 (6 × 5) | Short answer | 1, 2, 3 | CLO1, CLO4 |
| **B — Spot the Vulnerability** | 20 (4 × 5) | Name the flaw + CWE + the fix, from a code snippet | 3, 4, 5, 6 | CLO2, CLO3 |
| **C — Applied SQL Injection** | 30 (5 × 6) | Multi-part applied reasoning against a stated query | 4 | CLO2, CLO3 |
| **D — Defense & Design** *(the paper's own spelling)* | 20 (2 × 10) | Extended written answer | 4, 6 | CLO1, CLO3 |

**Read the coverage honestly before you claim it in a programme review.** CLO4 (security tooling
across the SDLC) rests on a *single 5-pt item* in Section A — this paper is not where CLO4 is
evidenced; the Week 2 worksheet and the tool-driven weeks are. CLO6 is carried by the paper's
ethics instruction line and by the integrity controls in §6, not by a marked item. CLO5
(evaluation and communication) is deliberately absent — the course specification §4 assigns no
CLO5 to the midterm row. Weighting is injection-heavy: Week 4 material carries Section C in full
plus one Section B item and one Section D item.

> **Known drift — reconcile before the cohort revises.** `labs/week08-midterm-written/README.md`'s
> *Format* list and `course-plan-19weeks.md:91` both summarise this exam as four things — threat
> modelling, CWE/OWASP mapping, spot-the-vuln, secure-design short answers — and neither mentions
> **Section C (30 pts)**. `slides/week08.md`'s *What's assessed* slide repeats the same four-item
> list, but that deck's separate *Format* slide already names all four sections in its presenter
> note ("sections A–D = concepts / spot-the-vuln / applied / design") — so the drift is in the
> README and the course plan, and in one slide of the deck, not the deck as a whole. A student
> revising from the README or course plan alone under-prepares for 30% of the paper. Either say so
> explicitly at the Week 7 debrief or fix the summaries.

## 3. Preparation before the day

- **Students, before the exam:** revise Weeks 1–6 (`labs/week08-midterm-written/README.md` step 1)
  using the Week 7 consolidation — cumulative review quiz `quizzes/quiz1.md`, Security Jeopardy and
  the mock CTF (`labs/week07-review-midterm-prep/mock-ctf.md`). Week 7's deliverable is a one-page
  cheat sheet, *eligible as an open-note aid if the instructor allows*.
- **Instructor, at the Week 7 debrief** (`AGENDA.md`, Week 7 block *Debrief: common mistakes +
  exam logistics*): announce the closed/open-note decision **before** students write the cheat
  sheet, and state which form of the paper is being sat.
- **Instructor, before the day:** confirm the exam version — the proctor deck's own note is to
  rotate from `instructor/exams/item-bank.md` each cohort. Produce the printed papers from the
  chosen form and check the code blocks survived printing (§11). Have the matching key to hand and
  only that key.
- **⬚** Room, seating plan, number of sections/sittings, invigilator roster, script paper and
  printing arrangements are not recorded in this repository.

## 4. The 120-minute block — logistics

`AGENDA.md` budgets **120 min** for the midterm written block and nothing else; it does not budget
briefing or settling time, so the pre-clock allowance is **⬚** and must come from the faculty's own
exam regulations. Order of business follows the proctor deck `slides/week08.md`:

| Step | Action | Source |
|---|---|---|
| Before the clock | Confirm the exam version aloud; state the duration, the closed/open-note rule and the integrity policy | `slides/week08.md` presenter notes |
| Before the clock | State the format: sections A–D, concepts / spot-the-vuln / applied / design, 100 pts | `slides/week08.md`, slide *Format* |
| Before the clock | State what is assessed and the single biggest score-saver — name the **fix** and the CWE, not just the bug | `slides/week08.md`, slides *What's assessed* / *Tips* |
| Before the clock | State: no phones, no AI | `slides/week08.md` presenter note |
| Clock starts | 120 min writing. Keep talking minimal once the clock starts | `AGENDA.md`; `slides/week08.md` presenter note |
| On the paper | Name, Student ID and Date fields are on the paper — check they are filled before collecting | `exam.md` header |
| At collection | Collect papers; remind the cohort that Week 9 is the hands-on CTF practical and their tools must be ready | `slides/week08.md` closing note |

**Materials allowed.** Three formulations exist in the repo and they reconcile as: *default closed
book* (`exam.md`: "Closed book unless stated otherwise"), instructor's discretion to run it
open-note (`labs/week08-midterm-written/README.md`), and the only documented permissible aid is a
**single one-page cheat sheet** (`instructor/anti-cheating.md` §C; the Week 7 deliverable). The
decision itself is **⬚** — record it here once made, because it changes what Week 7 asks students
to produce.

## 5. Forms A and B, and make-up sittings

The course specification §9 states the arrangement: *exams exist in two parallel forms (A/B) drawn
from a maintained item bank, supporting make-up sittings and reducing answer sharing.*

| Form | Where it lives | Status | Use |
|---|---|---|---|
| **A** | `labs/week08-midterm-written/exam.md` | **Public** — in the student-facing repo | The default sitting, *if* the cohort has not seen it |
| **B** | `instructor/exams/week08-midterm-written-formB.md` | Instructor-only (git-ignored) | Pre-assembled parallel form, same section weights as Form A; drawn from the MIDTERM POOL of `instructor/exams/item-bank.md` |

- Form B is built to the **same section weights** as Form A, so a Form B sitting is marked out of
  the same 100 pts and needs no scaling.
- Once Form B is deployed it becomes as public as Form A and must itself be rotated next cohort —
  `instructor/exams/item-bank.md` records that the public exam files are static and leak between
  cohorts.
- **Make-up sittings:** run the form the main cohort did *not* sit. Which form the main sitting
  used therefore has to be recorded on the day.
- **⬚** Make-up sitting date, eligibility rules and any cap on the make-up mark are institutional
  and not recorded in this repository.

## 6. Invigilation and academic integrity

Sourced from `instructor/anti-cheating.md` §C (*Written exams (W8/W18)*) and the `slides/week08.md`
presenter notes. Do **not** import the Google Form checklist from §C — that is scoped to the online
weekly quizzes, not to this paper.

- In-class and **monitored** throughout.
- **Multiple versions / shuffled sections** where the room allows it, and closed book — or the
  one-page cheat sheet only.
- **No phones, no AI**, stated aloud before the clock starts.
- The paper is individual work; the instruction line on the paper requires answers in the student's
  own words, which is also the marking stance (see §7).
- Identical wrong answers across adjacent scripts are the written-exam form of the red flag listed
  in `instructor/anti-cheating.md` §F. Keep the seating record so an adjacency claim can be checked
  later.
- **If copying is found:** follow `instructor/anti-cheating.md` §G — keep the evidence, apply the
  syllabus penalty consistently, and follow [ETHICS.md](../../ETHICS.md) plus **⬚** (institutional
  conduct process, as flagged in the course specification §11).

## 7. Marking

- **Who marks: ⬚.** The course specification names one instructor and records no TA, second-marker
  or moderation arrangement. If more than one person marks, fix a section split (one marker takes
  Section C across all scripts) so that a judgement call is at least applied consistently.
- **The key.** `instructor/exams/week08-midterm-written-answers.md` for Form A;
  `instructor/exams/week08-midterm-written-formB-answers.md` for Form B. Each key carries the
  per-question mark split and its own marking notes. Match the key to the deployed form before the
  first script — the two papers share section weights, which is exactly what makes a mismatched key
  easy to miss.
- **Borderline answers.** The course specification §8 sets the course-wide stance: partial credit
  is available for a correct mechanism explained without a working exploit. On this paper that
  translates to: a Section B answer that names the mechanism and the fix but misses the CWE id, or
  a Section C answer that explains why an injection works but writes it with a syntax slip, is a
  partial-credit case, not a zero. Decide each such class of answer **once**, write the ruling in
  the margin of your working copy of the key, and apply it to every script — then carry the ruling
  into §8 as a candidate item-bank note.
- **Score entry.** Enter the mark against **Midterm** in the gradebook; `instructor/GRADEBOOK.md`
  computes **Midterm % = average of W8 and W9**, so this paper is half of the 20% midterm
  component (course specification §4).
- **⬚** Grading scale / letter-grade boundaries (institutional).

## 8. After the exam — item analysis and the item bank

The repository defines the *loop* but not the *statistics*. Everything below that is not sourced is
marked ⬚ rather than guessed.

1. **Mark, then look at the paper rather than the students.** For each item, note where the cohort
   clustered: near-universal correct (the item discriminated nothing), near-universal wrong (the
   item was mis-set, mis-worded, or the teaching week did not land), and split-with-good-students-
   wrong (the item is probably ambiguous).
2. **Separate a bad item from a real gap.** If Section A's tooling item failed cohort-wide, that is
   a Week 2 signal, not a bad item — feed it to the Week 17 review rather than deleting the item.
3. **Replace, don't patch.** Items are rotated from the MIDTERM POOL of
   `instructor/exams/item-bank.md`, which exists for exactly this — the file states its purpose as
   rotating and rebuilding the written exams each cohort because the public exam files leak.
   `instructor/anti-cheating.md` §E requires rotating the question bank every cohort regardless of
   how the items performed.
4. **Write the ruling back.** Every borderline-answer ruling made in §7 is evidence that an item is
   ambiguous. Add it to the item's marking note in the bank, or reword the item, before it is used
   again.
5. **Close the loop on the forms.** Record which form this cohort sat, so the next cohort's Form A
   is not the paper this cohort has photographed.

**⬚ Not defined anywhere in this repository, and deliberately not invented here:** which item
statistic is used (facility index, discrimination index, point-biserial or none), the threshold at
which an item counts as discriminating poorly, who reviews the analysis, when it is done, and where
it is recorded. Fix these once and add them to `instructor/exams/item-bank.md`, not to this public
file.

## 9. Assessment for this week

| Instrument | Evidence | Outcome | Weight |
|---|---|---|---|
| Midterm written paper, Sections A–D | The script, 100 pts | K1–K3, P1–P3, A1–A2 | Half of the 20% midterm component (`instructor/GRADEBOOK.md`: Midterm % = average of W8, W9) |
| Invigilation record + seating record | Sitting conditions, form sat, incidents | A3 | Integrity control, not a mark |
| Item analysis (§8) | Per-item performance | Course-level, not student-level | Feeds the item bank and the Week 17 review |

No worksheet, no quiz and no flag this week — nothing is submitted to Classroom or GitHub.

## 10. Materials

- Paper, Form A (public): `labs/week08-midterm-written/exam.md`
- Week brief: `labs/week08-midterm-written/README.md`
- Proctor deck: `slides/week08.md` (Marp)
- Instructor-only, **never published**: `instructor/exams/week08-midterm-written-answers.md`,
  `instructor/exams/week08-midterm-written-formB.md`,
  `instructor/exams/week08-midterm-written-formB-answers.md`,
  `instructor/exams/item-bank.md`, `instructor/anti-cheating.md`, `instructor/GRADEBOOK.md`
- What students revised from: `labs/week07-review-midterm-prep/` (`quizzes/quiz1.md`,
  `mock-ctf.md`), the Week 1–6 lab folders
- Rules of engagement: [ETHICS.md](../../ETHICS.md)
- **⬚** Printed papers, script booklets, room booking

## 11. Risks and contingencies

| Risk | Mitigation |
|---|---|
| **Form A is published in the public repo** and, as `instructor/exams/item-bank.md` states, the public exam files are static and leak between cohorts — a repeating student or a shared drive from last year has the paper | Decide Form A vs Form B *before* the sitting; if there is any chance the cohort holds the paper, deploy Form B or rebuild Form A's items from the bank (`instructor/anti-cheating.md` §E) |
| A Form B sitting marked against Form A's key — the two share section titles and weights, so the mismatch is not obvious until the marks look strange | Write the form letter on the board and on the script header; open only the deployed form's key while marking |
| `instructor/` is git-ignored — a colleague marking from a fresh clone of the public repo has **no key at all**, and no Form B | Transfer the key out-of-band before marking day; never "fix" this by committing the key |
| The open-note decision is taken after Week 7 | The cheat sheet is a Week 7 deliverable; announcing the rule late makes that work either wasted or an unfair advantage for students who guessed right. Announce it in the Week 7 debrief slot |
| Printing a Markdown paper: Sections B and C are fenced code blocks. A wrapped or page-broken snippet changes what a "spot the vuln" item actually shows | Export to PDF once, read the printed proof line by line, and confirm no snippet wraps or splits across a page before duplicating |
| No lab block this week, so nothing is checked on a machine — Week 9 is a 150-min CTF practical and the first time anyone discovers a broken Docker install is at its start | Use the deck's closing note at collection: state that Week 9 tools must be ready, and post the Week 9 target check before students leave |
| Students revised from the README (`Format` list) or `course-plan-19weeks.md:91`, both of which omit Section C (30 pts) — see §2 | Say the section list aloud in the Week 7 debrief and at the pre-clock briefing (§4); reconcile the README and course-plan summaries afterwards |
| A student misses the sitting | Run the other form (§5); eligibility and date are **⬚** (institutional) |
| Multiple sections / multiple sittings of the same cohort | The later sitting must not sit the same form as the earlier one; record which form each section sat. Section and seating arrangements are **⬚** |

## 12. Post-teaching reflection

*Complete after the session — this also feeds the course's engagement data.*

- Attendance / completion: ⬚
- Form sat (A / B), and by which section: ⬚
- Time actually used by the cohort (did anyone need the full 120 min?): ⬚
- Section-by-section mark distribution, and which section was weakest: ⬚
- Items that discriminated poorly, and what replaced them in the bank: ⬚
- Borderline-answer rulings made during marking, and the item wording they imply: ⬚
- Integrity incidents, and how they were handled: ⬚
- Anything to change before this exam runs again: ⬚

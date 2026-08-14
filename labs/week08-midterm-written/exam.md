# Midterm — Written Exam (Week 8)

**Course:** Software Security (KOSEN69) · **Covers:** Weeks 1–6
**Time:** 120 min · **Total:** 100 pts · Closed book unless stated otherwise.

**Name:** ____________________  **Student ID:** ____________  **Date:** ________

> Answer in your own words. For code answers, write the exact payload/fix. Sandbox/ethics rules apply to all scenarios.

---

![A horizontal bar divided into four point-weighted blocks shows where the 100 exam marks fall: Section A, Concepts, 30 points across six independent 5-point items (CIA triad, STRIDE, SAST vs DAST vs SCA vs fuzzing, hashing vs encryption vs encoding, trust boundaries, least privilege and fail closed). Section B, Spot the Vulnerability, 20 points across four 5-point code-snippet items — name the flaw, cite the CWE, give the fix. Section C, Applied SQL Injection, 30 points as one continuous scenario, items C1 through C5, against a single vulnerable login query. Section D, Defense and Design, 20 points across two 10-point items on SQL injection defenses and secure password-reset design. Sections A and C are the two highest-value blocks at 30 points each, shown in the accent color; B and D are 20 points each, shown in the standard color. The exam covers Weeks 1 through 6, runs 120 minutes, and is closed book unless stated otherwise. It pairs with the Week 9 hands-on CTF practical.](img/exam-blueprint.svg)

## Section A — Concepts (30 pts, 5 each)

A1. Define the **CIA triad** and give one realistic threat against each property.

A2. Map each **STRIDE** letter to the security property it violates.

A3. Compare **SAST vs DAST vs SCA vs fuzzing** — what each sees and when it runs.

A4. Explain **hashing vs encryption vs encoding**, with one correct use of each.

A5. What is a **trust boundary**? Identify two in a typical web app + database.

A6. Define **least privilege** and **fail closed**, with one example each.

---

## Section B — Spot the Vulnerability (20 pts, 5 each)
*Name the vulnerability (+ CWE) and give the fix.*

B1.
```python
q = "SELECT * FROM users WHERE name='" + request.args["name"] + "'"
db.execute(q)
```

B2.
```python
return f"<h1>Hello {request.args['name']}</h1>"   # rendered in the browser
```

B3.
```python
data = jwt.decode(tok, options={"verify_signature": False})
if data["role"] == "admin": grant()
```

B4.
```python
import hashlib
def store(pw): return hashlib.md5(pw.encode()).hexdigest()
```

---

## Section C — Applied SQL Injection (30 pts)

A login runs this query (both fields are required, cannot be blank):
```sql
SELECT uid, name, salary, password FROM usertable
WHERE profileID = 10 AND password = '<hash>'
```

C1. (6) `profileID` is an **integer** parameter. What do you put in **profileID** and **password** to log in without the password? Explain why it works.

C2. (6) Now `profileID` is a **string** (`WHERE profileID='10' AND password='...'`). Give the injection and explain the difference from C1.

C3. (6) The form is submitted via **GET**: `/login?profileID=a&password=a`. Write the edited GET request to bypass auth, and explain the comment handling.

C4. (6) You can inject into an `UPDATE` on an edit-profile page. Write **three different** injections to fingerprint whether the DB is **MySQL/MSSQL, Oracle, or SQLite** (version).

C5. (6) Write a subquery to dump **all table names** from a SQLite DB into one field. (Hint: `group_concat` + `sqlite_master`.)

---

## Section D — Defense & Design (20 pts, 10 each)

D1. List **three** distinct defenses against SQL injection and explain why client-side validation is **not** one of them.

D2. You must add a "reset password" feature. Describe a secure design: token generation, storage, expiry, and how you avoid IDOR and account enumeration.

---

*End of exam. Pair with the Week 9 hands-on CTF practical.*

---
marp: true
theme: default
paginate: true
header: "Software Security · Week 3"
---

# Week 3
## Cryptography Used Correctly (and Misused)
Software Security · Nutthakorn Chalaemwongwan

<!-- Hook: paste an MD5 hash on screen and crack it live in seconds with a wordlist — "this is why how you store passwords matters." Today is about using crypto correctly; most failures are misuse, not broken math. ~2 min. -->

---

## Today

- Hashing vs encryption vs encoding
- Password storage done right
- Symmetric / asymmetric basics
- Common crypto failures (A04:2025)
- 🔓 Game: **Capture the Hash**

<!-- Roadmap, 1 min. Lab: crack weak hashes + break an ECB oracle, then remediate. Theme: "don't roll your own crypto; misuse vetted primitives correctly." -->

---

## Recap — Week 2

- Tools find bug *patterns*; today we study one bug *class* deeply
- Crypto misuse is subtle: code "works" but isn't safe

<!-- Bridge: a SAST tool flags MD5 (W2) — today we understand WHY it's wrong and what to do instead. ~1 min. -->

---

## Three things people confuse

- **Hashing** — one-way, fixed-size digest (integrity, passwords)
- **Encryption** — reversible *with a key* (confidentiality)
- **Encoding** — reversible *without a key* (Base64 ≠ security!)

<!-- The #1 source of crypto bugs is conceptual confusion. Demo: base64-decode a string live to show encoding gives no protection. Ask: "is hashing reversible?" (no) "is Base64?" (yes, trivially). ~5 min. -->

---

## Symmetric vs asymmetric

- **Symmetric** (AES, ChaCha20) — one shared key, fast
- **Asymmetric** (RSA, ECC) — public/private key pair
- TLS uses asymmetric to exchange a symmetric session key

<!-- Keep it intuitive: symmetric = one shared password (fast, but key distribution problem); asymmetric = padlock anyone can close, only you open. TLS = best of both. ~4 min. -->

---

## Password storage

- Never store plaintext or plain hashes
- Use a **slow, salted KDF**: argon2id (preferred), bcrypt, scrypt
- Salt is per-user and random

```python
from argon2 import PasswordHasher
ph = PasswordHasher(); hash = ph.hash("correct horse battery staple")
```

<!-- The single most common real-world crypto failure. Why slow + salted: slow defeats brute force, salt defeats rainbow tables and makes identical passwords hash differently. Tie to the hook (cracked MD5). ~6 min. -->

---

## Worked example: why ECB leaks

```text
plaintext blocks:   [AAAA][AAAA][BBBB][AAAA]
AES-ECB ciphertext: [ X  ][ X  ][ Y  ][ X  ]   ← same block → same cipher
```

- ECB encrypts each block independently → **patterns survive**
- The classic "ECB penguin": the image is still recognizable encrypted
- Fix: an authenticated mode (**AES-GCM**) with a random nonce

<!-- The visual that makes ECB "click". Walk the block mapping: identical plaintext → identical ciphertext, so structure leaks. Show the ECB-penguin image if you have it. This is exactly the ECB oracle they break in the lab. ~6 min. -->

---

## Capture the Hash — how cracking works

```bash
# strip comments, then crack unsalted MD5 with a wordlist
hashcat -m 0 hashes.txt rockyou.txt
```

- Unsalted fast hash → attacker hashes wordlist once, matches millions
- Salt would force per-guess work; a slow KDF makes it infeasible

<!-- Walk the attack: the attacker doesn't "reverse" the hash — they hash guesses and compare. Fast+unsalted = cheap; salted+slow = expensive. This is the lab's round 1. ~5 min. -->

---

## Common crypto failures (A04:2025)

- **ECB mode** → block patterns leak
- Hardcoded keys / keys in source (CWE-798)
- Weak RNG (`random` instead of `secrets`/CSPRNG) (CWE-330)
- **MD5 / SHA-1** for security; unauthenticated encryption (no integrity)

<!-- The checklist of what to look for / avoid. Each maps to a CWE they'll cite. Note: "no integrity" = attacker can flip ciphertext bits undetected → that's why AEAD (GCM) matters. ~4 min. -->

---

## Do this instead

- Authenticated encryption: **AES-GCM** or **ChaCha20-Poly1305**
- Keys from a secrets manager / KMS — never in code
- CSPRNG: `secrets` (Python), `crypto.randomBytes` (Node)
- SHA-256+ for integrity; argon2id/bcrypt for passwords

<!-- The "right answers" slide — students should leave able to pick the correct primitive. Emphasize: use vetted libraries, don't invent. ~3 min. -->

---

## CWE mapping

- **CWE-327** — broken/risky crypto algorithm
- **CWE-916** — weak password hash (no/weak KDF)
- **CWE-330** — insufficiently random values
- **CWE-798** — hardcoded key

<!-- Quick reference; they map lab findings to these. ~1 min. -->

---

## 🔓 Game — Capture the Hash

- **Round 1 (speedrun):** crack unsalted/MD5 hashes — fastest team wins
- **Round 2:** exploit an **ECB oracle** (identical blocks)
- **Round 3 (defend):** argon2id + AES-GCM + keys from env

<!-- Explain rounds before lab. Round 1 = instant-feedback fun; round 3 = the real learning (fix it). Leaderboard on round 1. ~3 min. -->

---

## Lab 3 — deliverable

> 📋 **Worksheet 3** — `labs/week03-cryptography/worksheet.md` (Part 3) · **kickoff:** `docker compose up` (runs the crypto scripts)

- Cracked hashes + method · ECB-leak proof · predictable-token note
- **Before/after** code (misuse → fix → CWE closed)
- **+ Audit the AI / EiPE / Prompt Problem** (see worksheet)

<!-- Graded output. Also: crack NoteVault's MD5 hashes for the project (worksheet). Point to vulnerable_crypto.py + solution_skeleton.py. -->

---

## Key takeaways

- Encoding ≠ encryption; hashing isn't reversible
- Use vetted KDFs + authenticated encryption — never roll your own
- Randomness & key handling matter as much as the algorithm

<!-- Recap. Cold-call: "how should we store passwords, and why salted+slow?" ~2 min. -->

---

# Questions?
Next week: Injection & input handling

<!-- Cliffhanger: "Next week — type one quote mark and log in as admin." Remind: hashcat + wordlist ready. -->

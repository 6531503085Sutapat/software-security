---
marp: true
theme: default
paginate: true
header: "Software Security · Week 11"
---

# Week 11
## Memory-Safety & Exploitation
Software Security · Nutthakorn Chalaemwongwan

<!-- Hook: feed random bytes to a C program until it crashes, then turn that crash into "execute my code." This week is the closest to classic hacking — and to why the world is moving to Rust. ~2 min. -->

---

## Today

- The C/C++ memory model & the stack
- Finding bugs with **fuzzing**
- Stack overflow → control hijack
- Mitigations + the **memory-safe language** shift
- 🎮 Game: **Fuzzing Race → Pwn the Binary**

<!-- Roadmap, 1 min. Arc of the week: find (fuzz) → understand (debug) → exploit (pwn) → defend (mitigations) → cure (Rust). Lab follows the same arc. -->

---

## Why this still matters

- C/C++ runs the world's critical infrastructure
- Memory bugs = ~70% of severe CVEs historically
- Now a national-policy issue (CISA/ONCD roadmaps)

<!-- Motivate hard. ~70% of Microsoft/Chrome severe CVEs are memory-safety bugs — that stat lands. It's now government policy (CISA Secure by Design, White House ONCD memory-safety report). This isn't legacy trivia; it's current. ~4 min. -->

---

## The stack frame

```text
[ buffer ][ saved registers ][ return address ]
                                    ↑ overwrite this
```

- `gets`/`strcpy`/unchecked `memcpy` → overflow
- Overwrite return address → redirect execution

<!-- The worked example — draw the stack on the board. A local buffer sits BELOW the saved return address; writing past the buffer marches upward into the return address. Control the return address = control where the CPU jumps next. This is THE concept of the week. ~8 min. -->

---

## Bug classes

- **CWE-121** stack overflow · **CWE-787** OOB write
- **CWE-416** use-after-free · **CWE-134** format string
- **CWE-193** off-by-one · integer overflow

<!-- Map the family. Note these aren't only stack overflows — UAF (free then use) and format-string are just as exploitable. CWE-787 (out-of-bounds write) was #1 in the CWE Top 25 for 2021–2023 (CWE-79/XSS retook #1 in 2024). ~3 min. -->

---

## Fuzzing — how bugs are found today

```bash
clang -fsanitize=address,fuzzer harness.c -o fuzz && ./fuzz   # libFuzzer
afl-fuzz -i seeds -o out -- ./vuln @@                          # AFL++
```

- Coverage-guided mutation finds crashes fast
- Pair with sanitizers (ASan) for root cause

<!-- Connect to W2 fuzzing (now hands-on). Coverage-guided = the fuzzer mutates inputs and keeps the ones that reach NEW code, so it "learns" its way to deep bugs. ASan turns a silent corruption into a precise crash report. This is round 1 of the game. ~6 min. -->

---

## Exploiting a stack overflow

1. Find offset to return address (cyclic pattern)
2. Overwrite RA → jump to `win()` / shellcode
3. Format string: `%x%x%x` leak, `%n` write

<!-- Walk the exploit method. Cyclic pattern (De Bruijn) tells you EXACTLY how many bytes until the return address. Then overwrite it with the address of win(). Format string: %x leaks stack, %n writes — a primitive most students haven't seen. This is round 2 (pwn). ~6 min. -->

---

## Mitigations raise the bar

- **Stack canaries** — detect overwrite before return
- **ASLR** — randomize addresses
- **NX/DEP** — no code execution on the stack
- **PIE** — position-independent executables
- …each makes the same exploit harder

<!-- Each defense breaks one step of the previous slide: canary detects the overwrite, NX stops shellcode-on-stack, ASLR/PIE hide the addresses. Key honest point: they raise cost, they don't eliminate the bug — attackers chain leaks to defeat them. ~5 min. -->

---

## The real fix: memory-safe languages

- **Rust / Go** remove whole bug classes by design
- CISA "Secure by Design" + ONCD: move off C/C++ for new code
- Borrow checker / bounds checks = no overflow, no UAF

<!-- The thesis of the week. Mitigations are a treadmill; memory-safe languages END the bug class. Rust's borrow checker makes UAF a compile error, not a CVE. This is exactly where industry + government are steering. ~4 min. -->

---

## 💥 Game — Fuzzing Race → Pwn the Binary

1. **Round 1 (Fuzzing Race):** first team to crash the target wins
2. **Round 2 (Pwn):** exploit the overflow / format string
3. **Round 3 (Defend):** rebuild with canary+ASLR+PIE, then **rewrite in Rust**

<!-- Explain the 3 rounds before lab. Round 1 = instant feedback (it crashes or not). Round 3 (defend + Rust rewrite) is graded and the real lesson. Q6 of the quiz asks for the crashing input + the defense. ~3 min. -->

---

## Deliverable

> 📋 **Worksheet 11** — `labs/week11-memory-safety-exploitation/worksheet.md` (Part 3) · **kickoff:** in the **toolbox container** (`labs/toolbox`): `clang -fsanitize=address,fuzzer fuzz_harness.c -o fuzz && ./fuzz`

- Fuzzing crash + exploit script
- Annotated Ghidra/gdb analysis
- Memory-safe (Rust) rewrite + why the bug is now impossible
- **+ Audit the AI / EiPE / Prompt Problem** (see worksheet)

<!-- The Rust rewrite + "why it's now impossible" is the key deliverable — it proves they understand the cure, not just the exploit. AI-resilient tasks count. -->

---

## Key takeaways

- Fuzz to find, debug to understand, mitigate to slow attackers
- Mitigations ≠ cure — memory-safe languages are the cure
- This is where the industry is moving

<!-- Recap. Cold-call: "why aren't stack canaries enough?" (they detect, don't prevent; bypassable via leaks — the cure is memory safety). ~2 min. -->

---

# Questions?
Next week: Software supply-chain security

<!-- Cliffhanger: "Next week — one poisoned dependency owns thousands of victims; we'll replay xz and SolarWinds-style attacks." -->

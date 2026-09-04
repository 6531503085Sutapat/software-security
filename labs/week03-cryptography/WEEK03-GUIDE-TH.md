# Week 3 — Cryptography: แนวทางทำทั้งหมด 🔐
> Study guide by รุ่นพี่สาย Security · สำหรับ Sutapat (6531503085)
> **นี่คือ "แนวทาง" ไม่ใช่ "เฉลย"** — พี่บอกวิธี + คำใบ้ + จุดพลาดบ่อย ส่วนคำตอบน้องคิด/เขียนเองนะ 💪
> OWASP 2025 **A04 Cryptographic Failures** · CWE-327, CWE-916, CWE-330, CWE-798

---

## 🗺️ ลำดับการลุยที่พี่แนะนำ
ทำเรียงแบบนี้จะลื่นสุด (ง่าย → ยาก, และหลักฐานต่อยอดกันได้):

`Setup → Task 0 → Task 4 → Task 2 → Task 3 → Task 1 → Task 6/7/9 → Task 8 → Task 5 → งานเขียน`

เหตุผล: เก็บของง่ายที่เห็นผลทันที (0,4,2,3) ก่อน แล้วค่อยไป crack (1,5) กับ remediate (6/7/9) ที่ใช้เวลา แล้วปิดท้ายด้วยงานเขียนตอนเข้าใจครบแล้ว

---

## ⚠️ กฎเหล็ก: Evidence & Integrity (อ่านก่อน ไม่งั้นเสียคะแนนฟรี)
ทุก screenshot **ต้องมี terminal ที่รันคำสั่งนี้อยู่ในรูปเดียวกัน** กับหลักฐาน:
```bash
printf '%s | %s | ' "$(whoami)" '6531503085'; date '+%F %T %Z'
```
- output ของ lab มัน **เหมือนกันทั้งรุ่น by design** → stamp ชื่อ+รหัส+เวลา คือสิ่งเดียวที่พิสูจน์ว่าเป็นของน้อง
- ถ้าหลักฐานเป็นหน้า browser/DevTools → วาง terminal **ข้างๆ แล้วแคปทั้งจอ** (อย่า crop เฉพาะหน้าต่าง)
- ห้ามยืมรูปเพื่อน / รูปที่ไม่มี stamp = ไม่รับ

---

## 🛠️ Setup Environment
```bash
cd labs/week03-cryptography
docker compose up          # ลง pycryptodome + argon2-cffi แล้วรันทั้ง 2 สคริปต์ให้เลย
# หรือ local:
pip install pycryptodome argon2-cffi
python vulnerable_crypto.py
```
ไฟล์ที่เกี่ยวข้อง: `vulnerable_crypto.py` (ของพัง), `hashes.txt` (4 MD5), `solution_skeleton.py` (ของแก้แล้ว)

---

## 📝 Part 2 — Lecture Questions (ตอบด้วยภาษาตัวเอง 2–4 ประโยค/ข้อ)
พี่จะให้ "จุดที่ต้องพูดถึง" ไม่ใช่ประโยคสำเร็จรูป — เอาไปเรียบเรียงเองนะ

**Q1. Hashing vs Encryption vs Encoding — และงานที่แต่ละตัวใช้ผิด**
- Hashing = one-way (ย้อนไม่ได้) → ใช้ตรวจ integrity / เก็บ password. *ใช้ผิด:* เอาไป "เก็บความลับที่ต้องอ่านคืน"
- Encryption = two-way + ต้องมี key → ใช้ปกป้องความลับที่ต้องถอดคืนได้. *ใช้ผิด:* เอาไปเก็บ password (ถ้า key หลุด = password หลุดหมด)
- Encoding = แปลงรูปแบบ (Base64/URL) **ไม่ใช่ security เลย** ใครก็ decode ได้. *ใช้ผิด:* คิดว่ามันคือการเข้ารหัส
- 💡 analogy: hashing = เครื่องบดเนื้อ (บดแล้วคืนไม่ได้), encryption = ตู้เซฟมีกุญแจ, encoding = แปลภาษา (ใครมี dict ก็อ่านออก)

**Q2. ทำไม MD5/SHA-1 ไม่เหมาะเก็บ password / ใช้อะไรแทน**
- key point: มันออกแบบมาให้ **เร็ว** → attacker ยิงเดาได้พันล้านครั้ง/วิ (GPU) → เหมาะ integrity ไม่เหมาะ password
- ใช้แทน: **KDF ที่จงใจให้ช้า/กิน memory** → bcrypt / scrypt / **argon2id**

**Q3. Salt คืออะไร กันอะไร ทำไมต้อง unique ต่อ password**
- salt = ค่าสุ่มที่เติมก่อน hash
- กัน: **rainbow tables** + กันการเห็นว่า user 2 คนใช้ password เดียวกัน
- ต้อง unique เพราะถ้า salt เดียวกันหมด → ยัง precompute/เทียบ password ซ้ำได้อยู่

**Q4. ทำไม AES-ECB leak structure / AES-GCM เพิ่มอะไร**
- ECB: block เท่ากัน → ciphertext เท่ากัน → เห็น pattern (คำสำคัญให้เสิร์ช: "ECB penguin 🐧")
- GCM เพิ่ม **integrity/authenticity** ผ่าน auth tag → ถ้าใครแก้ ciphertext แม้ 1 byte, decrypt จะ fail (AEAD)

**Q5. `random` vs CSPRNG (`secrets`) — สำคัญตรงไหน**
- `random` = Mersenne Twister, **predictable** (ทำนาย state ได้ถ้ารู้ output พอ) → ใช้ทำเกม/สุ่มทั่วไปได้ แต่ห้ามงาน security
- `secrets` / `os.urandom` = CSPRNG → ใช้กับ token, key, password reset, session id
- สำคัญตรงไหน: อะไรก็ตามที่ "attacker เดาได้แล้วซวย"

---

## 🧪 Part 3 — Hands-on Tasks (method + pitfalls)

### Task 0 — Onboarding (5 min)
รัน `python vulnerable_crypto.py` → screenshot output (md5 / ecb hex / token) พร้อม stamp
**ส่ง:** screenshot อย่างเดียว

### Task 1 — Capture the Hash 🔓 (30 min) *— ห้ามลอก, ต้อง crack เอง*
1. ลบบรรทัด comment (`#`) ใน `hashes.txt` ออกก่อน (เหลือแต่ hash 4 บรรทัด)
2. รัน: `hashcat -m 0 hashes.txt rockyou.txt` (`-m 0` = raw MD5)
   - หรือ john: `john --format=raw-md5 --wordlist=rockyou.txt hashes.txt`
3. **ทางเลือกถ้าลง hashcat ยาก** — เขียน mini-cracker เองเข้าใจกลไกกว่า:
   ```python
   import hashlib
   targets = set(open("hashes.txt").read().split())
   for w in open("wordlist.txt", encoding="latin-1", errors="ignore"):
       w = w.strip()
       if hashlib.md5(w.encode()).hexdigest() in targets:
           print(w)
   ```
   4 ตัวนี้เป็น password **ยอดฮิตที่สุดในโลก** — wordlist เล็กๆ ก็เจอ (คำใบ้: นึกถึง password ที่คนขี้เกียจใช้กันที่สุด 🙈)
**ส่ง:** screenshot ผลที่ crack ได้ + 1 บรรทัดว่าทำไม unsalted MD5 ล่มเร็ว (CWE-916/327)
**Pitfall:** ลืมลบ comment → hashcat error / ลืม `-m 0`

### Task 2 — ECB structure leak (20 min)
เรียก `encrypt_ecb(b"A"*16 + b"A"*16)` แล้วดู `.hex()`
→ ตัด hex เป็นก้อนละ 32 ตัวอักษร (= 16 byte) จะเห็น **block 1 = block 2 เป๊ะ**
**ส่ง:** hex output ที่ highlight block ที่ซ้ำ + อธิบายว่า leak structure ยังไง (CWE-327)

### Task 3 — Predictable token (15 min)
เรียก `reset_token()` หลายรอบ → มันคือ 6 หลัก = **10^6 = 1,000,000** ความเป็นไปได้
- attack estimate: server รับ ~1000 req/s → ยิงหมดใน ~1000 วิ (< 20 นาที) และไม่ใช่ CSPRNG ด้วย
**ส่ง:** ตัวอย่าง token หลายอัน + 1 บรรทัด attack estimate (CWE-330)

### Task 4 — Hardcoded key (5 min)
ชี้บรรทัด `HARDCODED_KEY = b"0123456789abcdef"`
- ทำไมผิด: key อยู่ใน source → ใครเห็น repo/binary ก็ถอดรหัสได้หมด, rotate ยาก (CWE-798)
- mitigation (2 ประโยค): ดึง key จาก **env var / secrets manager (KMS/Vault)**, ห้าม commit, rotate ได้
**ส่ง:** บรรทัดนั้น + mitigation

### Task 5 — Crack the project target (NoteVault) (25 min)
- NoteVault เก็บ unsalted MD5 → หา hash มาจาก `/admin` (พอเข้าถึงได้) หรือจาก `seed()`
- crack ด้วย `hashcat -m 0` เหมือน Task 1
**ส่ง:** password ที่ได้ + CWE + **บันทึกลง `project/REPORT-TEMPLATE.md`**

### Task 6 — Password storage migration (25 min)
- เขียน `store_password`/`verify_password` ด้วย **argon2id** (มีใน `solution_skeleton.py` แล้ว — เข้าใจมันให้ได้)
- ส่วนที่ต้องคิดเพิ่ม: **rehash-on-login** — ตอน login ถ้าเจอ record เป็น MD5 เก่า → verify ผ่านแล้ว **อัพเกรดเป็น argon2id ทันที**
  ```python
  # pseudo
  if looks_like_md5(stored):
      if md5(pw) == stored:          # legacy verify
          stored = ph.hash(pw)       # upgrade + save
          return True
  else:
      return verify_password(stored, pw)
  ```
**ส่ง:** code + note ว่าทำไม migration สำคัญ (อัพเกรดได้โดยไม่ต้อง reset ทุกคน)

### Task 7 — Authenticated encryption round-trip (20 min)
- encrypt+decrypt ด้วย **AES-GCM**, nonce สุ่ม 12 byte, key จาก env
- **trick สำคัญ:** หลัง encrypt → **พลิก 1 byte ของ ciphertext** → decrypt ใหม่ → ต้อง **throw error (tag check fail)**
**ส่ง:** round-trip output + proof ว่า tampered แล้ว fail (นี่คือจุดที่ GCM > ECB)
**Pitfall:** ต้องเก็บ `nonce` + `tag` ไว้ตอน decrypt ด้วย ไม่งั้นถอดไม่ได้

### Task 8 — TLS in practice (15 min)
```bash
openssl s_client -connect example.com:443 </dev/null 2>/dev/null \
  | tee /tmp/tls.txt | openssl x509 -noout -issuer -subject -dates
grep -E 'Protocol|New,' /tmp/tls.txt      # ได้ TLS version
```
**ส่ง:** cert summary (issuer/subject/dates) + TLS version + 1 บรรทัดว่า TLS ปกป้องอะไรที่ hashing/at-rest ไม่ได้ (คำใบ้: **data in transit**)

### Task 9 — Defend / fix it (20 min)
รัน `python solution_skeleton.py` ให้ผ่าน → ยืนยันว่า:
| ของพัง (misuse) | ของแก้ (fix) | CWE ที่ปิด |
|---|---|---|
| MD5 no salt | argon2id (auto-salt) | CWE-916 / CWE-327 |
| AES-ECB | AES-GCM (nonce + tag) | CWE-327 |
| 6-digit `random` token | `secrets.token_urlsafe` | CWE-330 |
| HARDCODED_KEY | key จาก `ENC_KEY_HEX` env | CWE-798 |
**ส่ง:** ตาราง before→after→CWE + screenshot สคริปต์ที่แก้แล้วรันได้

---

## 🤔 Part 4 — Reflection
1. map 4 misuse → CWE → OWASP A04 (บรรทัดละอัน) — ใช้ตาราง Task 9 ต่อยอดได้
2. หา **breach จริง** ที่เกิดจาก weak hashing / hardcoded key + fix ไหนในนี้จะกันได้
   - 💡 ตัวจริงที่น้องไปหาข้อมูลเพิ่มได้ (verify เองก่อนเขียน): **LinkedIn 2012** (unsalted SHA-1), **Adobe 2013** (ใช้ 3DES-ECB + hint แทน hash ที่ salt), **RockYou 2009** (เก็บ plaintext → กลายเป็น `rockyou.txt` ที่น้องใช้อยู่นี่แหละ)
3. ในบรรดา 4 fix — อันไหนปิดความเสี่ยงจริงมากสุด เพราะอะไร (คิดเรื่อง blast radius: password reuse ข้ามเว็บ)

---

## 🤖 Audit the AI (required — ให้คะแนนที่การ *วิจารณ์* AI)
1. ถาม AI ให้ exploit **หรือ** fix ช่องโหว่สัปดาห์นี้ → paste คำตอบเต็ม
2. **หาจุดผิด/เสี่ยง**: โค้ดไม่ปลอดภัย, fix ไม่ครบแบบเนียนๆ, **API/CVE ที่ AI มโนขึ้น (hallucinate)**, edge case ที่พลาด, เหตุผลผิด → quote บรรทัดเป๊ะๆ
3. ทำ version ที่ถูก+verify เอง + อธิบาย 2–3 ประโยคว่าทำไมของ AI ไม่พอ
- 💡 จุดที่ AI มักพลาดเรื่อง crypto: ลืม auth tag, ใช้ nonce ซ้ำ, แนะนำ MD5/SHA-256 เปล่าๆ เก็บ password, hardcode key ในตัวอย่าง
> อย่าลืม disclose การใช้ AI ในตาราง Part 1

---

## 🧠 Comprehension & Prompt (required)
**A. EiPE (Explain in Plain English):** 2–3 ประโยค อธิบายว่าโค้ด/endpoint สัปดาห์นี้ *ทำอะไร* และ *ทำไมถึง exploit ได้* — เน้น **กลไก** ไม่ใช่โยน jargon

**B. Prompt Problem:** เขียน prompt **เดียว** ที่ทำให้ AI ออก fix ที่ถูก+ปลอดภัยสำหรับ 1 finding → รันดูว่า exploit fail ไหม ถ้ายัง → refine prompt แล้วลองใหม่ → ส่ง **prompt สุดท้าย + ผลที่ verify แล้ว**
- 💡 prompt ดี = ระบุ: ภาษา/lib, algorithm ที่ต้องใช้ (argon2id/AES-GCM), constraint (no hardcoded key), และ "ต้องผ่าน test ไหน"

---

## ✅ Submission Checklist
- [ ] Part 1: กรอกชื่อ/รหัส/วันที่/กลุ่ม + disclose AI
- [ ] Part 2: ตอบ 5 ข้อ ด้วยภาษาตัวเอง
- [ ] Task 0–9: หลักฐานครบ + **ทุกรูปมี identity stamp**
- [ ] Task 5: บันทึก finding ลง `project/REPORT-TEMPLATE.md`
- [ ] Part 4: reflection 3 ข้อ (breach ต้องเป็นของจริง)
- [ ] Audit the AI + EiPE/Prompt
- [ ] ส่ง: worksheet PDF → `learn.zcr.ai/submit` · code → GitHub · quiz → `learn.zcr.ai/quiz` (ดู `SUBMISSION.md`)

**Rubric:** Lecture 20 · Exploitation+evidence 40 · Defense 25 · Reflection 15 = 100

---
*ติดตรงไหนทักพี่ได้เลยนะ ถ้าอยากได้เฉลยข้อไหนเต็มๆ บอก "ขอเฉลย" ได้ 😄*

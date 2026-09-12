import hashlib, os
CANDIDATES = ["rockyou.txt", "/usr/share/wordlists/rockyou.txt"]
wl = next((p for p in CANDIDATES if os.path.exists(p)), None)
if not wl:
    raise SystemExit("rockyou.txt not found — วางไว้ในโฟลเดอร์นี้ หรือ /usr/share/wordlists/")
targets = {l.strip() for l in open("hashes.txt")
           if l.strip() and not l.startswith("#")}
found = {}
with open(wl, encoding="latin-1", errors="ignore") as f:
    for line in f:
        w = line.strip()
        h = hashlib.md5(w.encode()).hexdigest()
        if h in targets:
            found[h] = w
            print(f"{h} -> {w}")
        if len(found) == len(targets):
            break
print(f"\ncracked {len(found)}/{len(targets)}  (wordlist: {wl})")

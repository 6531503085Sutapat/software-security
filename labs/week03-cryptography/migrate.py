import hashlib
from argon2 import PasswordHasher

ph = PasswordHasher()

def looks_like_md5(stored: str) -> bool:
    
    s = stored.lower() //Robust case
    return len(s) == 32 and all(c in "0123456789abcdef" for c in s)

def verify_and_upgrade(stored: str, pw: str):
    
    if looks_like_md5(stored):
        # Old legacy path: verify MD5 
        if hashlib.md5(pw.encode()).hexdigest() == stored.lower():
            return True, ph.hash(pw)        # password ถูก -> อัพเกรดเป็น argon2id
        return False, None
    else:
        # argon2id -> just verify  not upgrade
        try:
            return ph.verify(stored, pw), None
        except Exception:
            return False, None

# ===== test =====
legacy = hashlib.md5(b"password").hexdigest()
print("stored (legacy):", legacy)
ok, new = verify_and_upgrade(legacy, "password")
print("1) login ok:", ok, "| upgraded?", new is not None)
ok2, new2 = verify_and_upgrade(new, "password")
print("2) login ok:", ok2, "| upgraded?", new2 is not None)
ok3, _ = verify_and_upgrade(legacy, "wrongpass")
print("3) wrong pw ok:", ok3)

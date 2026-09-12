from argon2 import PasswordHasher
ph = PasswordHasher()
def store_password(pw: str) -> str:
    return ph.hash(pw)
def verify_password(stored_hash: str, pw: str) -> bool:
    try: return ph.verify(stored_hash, pw)
    except Exception: return False
h1 = store_password("password123")
h2 = store_password("password123")
print("same pw -> different hashes?:", h1 != h2)
print("verify correct:", verify_password(h1, "password123"))
print("verify wrong:", verify_password(h1, "wrong"))

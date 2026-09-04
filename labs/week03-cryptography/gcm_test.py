import os
from Crypto.Cipher import AES

key  = os.urandom(32)
data = b"transfer $100 to alice"

# --- encrypt ---
nonce = os.urandom(12)
ct, tag = AES.new(key, AES.MODE_GCM, nonce=nonce).encrypt_and_digest(data)

# --- 1) decrypt ปกติ -> ผ่าน ---
pt = AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt_and_verify(ct, tag)
print("clean decrypt OK :", pt)

# --- 2) พลิก 1 byte ของ ciphertext -> ต้อง fail ---
bad = bytearray(ct); bad[0] ^= 0x01          # flip 1 bit
try:
    AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt_and_verify(bytes(bad), tag)
    print("!! tampered SUCCEEDED (ไม่ควรเกิด)")
except ValueError as e:
    print("tampered decrypt FAILED as expected :", e)

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import auth


def test_password_roundtrip():
    h = auth.hash_password("s3cret-pw")
    assert h != "s3cret-pw"                       # not plaintext
    assert auth.verify_password("s3cret-pw", h)
    assert not auth.verify_password("wrong", h)


def test_invite_code_check():
    assert auth.invite_ok("LETMEIN", "LETMEIN")
    assert not auth.invite_ok("nope", "LETMEIN")
    assert not auth.invite_ok("anything", "")     # unset invite code => registration closed


def test_csrf_token_verify():
    tok = auth.new_csrf_token()
    assert auth.csrf_ok(tok, tok)
    assert not auth.csrf_ok(tok, "other")
    assert not auth.csrf_ok(tok, None)

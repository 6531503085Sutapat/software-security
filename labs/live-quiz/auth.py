# auth.py — password hashing, invite-code registration gate, CSRF tokens, and a
# login_required guard for the platform's teacher-facing routes.
import functools
import hmac
import secrets

import bcrypt
from flask import session, redirect, url_for, request, abort


def hash_password(pw):
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(pw, stored_hash):
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), stored_hash.encode("ascii"))
    except (ValueError, AttributeError):
        return False


def invite_ok(supplied, configured):
    # constant-time compare; an empty/unset configured code closes registration entirely
    if not configured:
        return False
    return hmac.compare_digest(str(supplied or ""), str(configured))


def new_csrf_token():
    return secrets.token_urlsafe(32)


def csrf_ok(session_token, form_token):
    if not session_token or not form_token:
        return False
    return hmac.compare_digest(str(session_token), str(form_token))


def current_teacher_id():
    return session.get("teacher_id")


def login_required(view):
    @functools.wraps(view)
    def wrapped(*a, **kw):
        if current_teacher_id() is None:
            return redirect(url_for("login_page", next=request.path))
        return view(*a, **kw)
    return wrapped

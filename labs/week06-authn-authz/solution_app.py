"""Secure version — Week 6 Authentication & Access Control. Fixes IDOR and JWT handling."""
import os
import datetime
import jwt  # pip install pyjwt
from flask import Flask, request, jsonify

app = Flask(__name__)

# FIX CWE-321/798: strong secret from the environment (fallback only for local lab runs).
SECRET = os.environ.get("JWT_SECRET") or os.urandom(32).hex()
AUDIENCE = "week06-lab"

USERS = {"alice": "alicepw", "bob": "bobpw"}
ORDERS = {
    1: {"owner": "alice", "item": "Laptop", "total": 1200},
    2: {"owner": "bob", "item": "Phone", "total": 800},
}


@app.route("/")
def index():
    return jsonify(
        lab="Week 6 — Auth & Access Control (FIXED)",
        endpoints={"POST /login": "JSON {user, pw} -> JWT",
                   "GET /api/orders/<id>": "now enforces ownership"},
        note="Cross-user access and forged tokens should now be rejected.",
    )


@app.route("/login", methods=["POST"])
def login():
    user = request.json.get("user")
    pw = request.json.get("pw")
    if USERS.get(user) != pw:
        return jsonify(error="bad credentials"), 401
    # FIX: include expiry and audience so tokens are short-lived and scoped.
    payload = {
        "sub": user,
        "aud": AUDIENCE,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15),
    }
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    return jsonify(token=token)


def current_user():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "")
    # FIX CWE-347: pin a single algorithm (no 'none'), verify signature, exp, and audience.
    data = jwt.decode(token, SECRET, algorithms=["HS256"], audience=AUDIENCE, options={"require": ["exp", "aud"]})
    return data.get("sub")


@app.route("/api/orders/<int:oid>")
def get_order(oid):
    try:
        user = current_user()
    except jwt.InvalidTokenError:
        return jsonify(error="invalid token"), 401
    order = ORDERS.get(oid)
    if not order:
        return jsonify(error="not found"), 404
    # FIX CWE-639: deny-by-default ownership check on every object access.
    if order["owner"] != user:
        return jsonify(error="forbidden"), 403
    return jsonify(order)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

"""
Week 2 Task 8 - remediated version of vulnerable-repo/app.py.
Each fix is mapped to the CWE it closes.
"""
import os
import re
import sqlite3
import subprocess

import bcrypt
from flask import Flask, request

# Hostname / IPv4 allowlist: letters, digits, dot, hyphen - but NOT starting with
# a hyphen, so a value like "-f" can never be parsed by ping as a flag
# (argument injection). Length-capped to keep the regex cheap.
HOST_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-]{0,253}$")

app = Flask(__name__)

# FIX CWE-798: secrets come from the environment, never from source.
# The leaked lab values must also be ROTATED - removing them from code does not
# un-leak a credential that was already committed.
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
DB_PASSWORD = os.environ["DB_PASSWORD"]


@app.route("/user")
def user():
    name = request.args.get("name", "")
    con = sqlite3.connect("app.db")
    # FIX CWE-89: parameterized query - the driver sends the value separately
    # from the SQL text, so it can never be parsed as SQL syntax.
    rows = con.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchall()
    return str(rows)


@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    # FIX CWE-78, layer 1: validate the input against an allowlist BEFORE use.
    if not HOST_RE.match(host):
        return "invalid host", 400
    # FIX CWE-78, layer 2: no shell, argument list - the OS execs `ping`
    # directly and `host` is one argv entry, so shell metacharacters
    # (; | && $() `) are passed as literal text and never interpreted.
    try:
        return subprocess.check_output(
            ["ping", "-c", "1", host], shell=False, timeout=5
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "ping failed", 502


def store_password(pw):
    # FIX CWE-327: bcrypt - salted and deliberately slow, so offline cracking
    # is expensive. Verify with bcrypt.checkpw(pw.encode(), stored_hash).
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt())


if __name__ == "__main__":
    # FIX CWE-489: debug is off unless explicitly enabled for local dev.
    app.run(debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")
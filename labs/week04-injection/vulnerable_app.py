"""Deliberately INSECURE — Week 4 Injection & Input Handling. Sandbox only; for authorized lab use."""
import os
import sqlite3
import subprocess
from flask import Flask, request, g

app = Flask(__name__)
DB = "/tmp/week04.db"
UPLOAD_DIR = "/tmp/uploads"
FLAG_SQLI = os.environ.get("FLAG_SQLI", "FLAG{sqli_demo}")
FLAG_CMDI = os.environ.get("FLAG_CMDI", "FLAG{cmdi_demo}")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
    return g.db


@app.teardown_appcontext
def close_db(exc):
    d = g.pop("db", None)
    if d is not None:
        d.close()


def seed():
    con = sqlite3.connect(DB)
    con.execute("DROP TABLE IF EXISTS users")
    con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    con.executemany("INSERT INTO users (username, password) VALUES (?, ?)",
                    [("alice", "alicepw"), ("bob", "bobpw"), ("admin", FLAG_SQLI)])
    con.commit()
    con.close()
    # Per-student command-injection flag on disk -> reachable via /ping?host=;cat /flag.txt
    try:
        open("/flag.txt", "w").write(FLAG_CMDI + "\n")
    except Exception:
        pass


@app.route("/")
def index():
    return (
        "Week 4 — Injection lab (VULNERABLE; sandbox only)\n"
        "Endpoints:\n"
        "  /login?user=&pw=   SQLi auth bypass\n"
        "  /search?q=         SQLi (try UNION)\n"
        "  /ping?host=        OS command injection\n"
        "  /upload            unrestricted file upload (GET form / POST field f)\n",
        200,
        {"Content-Type": "text/plain; charset=utf-8"},
    )


@app.route("/login")
def login():
    user = request.args.get("user", "")
    pw = request.args.get("pw", "")
    # CWE-89: SQL injection — user input concatenated straight into the query.
    # Try:  /login?user=alice'--&pw=x   or   /login?user=x' OR '1'='1'--&pw=x
    q = "SELECT id, username FROM users WHERE username = '%s' AND password = '%s'" % (user, pw)
    row = db().execute(q).fetchone()
    return ("Welcome %s\n" % row[1]) if row else "Login failed\n"


@app.route("/search")
def search():
    term = request.args.get("q", "")
    # CWE-89: SQL injection in a LIKE search.  Try:  /search?q=' UNION SELECT username,password FROM users--
    q = "SELECT id, username FROM users WHERE username LIKE '%%%s%%'" % term
    return "\n".join("%s:%s" % r for r in db().execute(q).fetchall()) + "\n"


@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    # CWE-78: OS command injection — shell=True with attacker-controlled input.
    # Try:  /ping?host=127.0.0.1;id    or   /ping?host=$(whoami)
    out = subprocess.run("ping -c 1 " + host, shell=True, capture_output=True, text=True)
    return "<pre>%s</pre>" % (out.stdout + out.stderr)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        return '<form method=post enctype=multipart/form-data><input type=file name=f><input type=submit></form>'
    f = request.files["f"]
    # CWE-434: unrestricted file upload — any extension saved to a served dir -> upload a .py/.sh and get RCE.
    dest = os.path.join(UPLOAD_DIR, f.filename)
    f.save(dest)
    return "saved to %s\n" % dest


if __name__ == "__main__":
    seed()
    app.run(host="0.0.0.0", port=5000, debug=True)

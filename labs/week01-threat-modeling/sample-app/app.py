"""
Tiny sample web app for Week 1 threat modeling.
You will NOT exploit this in Week 1 — you will draw a data-flow diagram
and apply STRIDE to its components (web client, app, SQLite DB, /upload).
"""
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import sqlite3, os

app = Flask(__name__)
DB = "notes.db"
UPLOAD_DIR = os.path.abspath("uploads")
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.pdf'}
os.makedirs(UPLOAD_DIR, exist_ok=True)

def init_db():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, owner TEXT, body TEXT)")
    con.commit(); con.close()

def is_extension_allowed(filename):
    if not filename:
        return False
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_EXTENSIONS

@app.route("/notes", methods=["GET", "POST"])
def notes():
    con = sqlite3.connect(DB)
    if request.method == "POST":
        owner = request.json.get("owner", "anon")
        body = request.json.get("body", "")
        con.execute("INSERT INTO notes (owner, body) VALUES (?, ?)", (owner, body))
        con.commit()
    rows = con.execute("SELECT id, owner, body FROM notes").fetchall()
    con.close()
    return jsonify(rows)

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    f = request.files["file"]

    if f.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not is_extension_allowed(f.filename):
        return jsonify({"error": "Extension not allowed"}), 415

    filename = secure_filename(f.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    target_path = os.path.join(UPLOAD_DIR, filename)
    real_path = os.path.abspath(target_path)
    safe_dir = UPLOAD_DIR + os.sep

    if not real_path.startswith(safe_dir):
        return jsonify({"error": "Path traversal attempt detected"}), 403

    f.save(real_path)
    return jsonify({
        "message": "File uploaded successfully",
        "filename": filename
    }), 200

@app.route("/files/<name>")
def files(name):
    return send_from_directory(UPLOAD_DIR, name)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
    
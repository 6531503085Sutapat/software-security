"""
Tiny sample web app for Week 1 threat modeling.
"""
import os
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
DB = "notes.db"
UPLOAD_DIR = os.path.abspath("uploads")
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.pdf'}

os.makedirs(UPLOAD_DIR, exist_ok=True)

def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, owner TEXT, body TEXT)")
        con.commit()

def is_extension_allowed(filename):
    if not filename or '.' not in filename:
        return False
    # os.path.splitext safely extracts the final extension
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_EXTENSIONS

@app.route("/notes", methods=["GET", "POST"])
def notes():
    with sqlite3.connect(DB) as con:
        if request.method == "POST":
            owner = request.json.get("owner", "anon")
            body = request.json.get("body", "")
            # Parameterized query prevents SQL injection
            con.execute("INSERT INTO notes (owner, body) VALUES (?, ?)", (owner, body))
            con.commit()
        rows = con.execute("SELECT id, owner, body FROM notes").fetchall()
    return jsonify(rows)

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    f = request.files["file"]

    if f.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # FIX 1: Strict File Extension Allow-list
    if not is_extension_allowed(f.filename):
        return jsonify({"error": "Extension not allowed"}), 415

    # FIX 2a: Filename Sanitization (Base defense)
    # Strips out path manipulation characters like '../'
    filename = secure_filename(f.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    target_path = os.path.join(UPLOAD_DIR, filename)
    real_path = os.path.abspath(target_path)

    # FIX 2b: Final Path Resolution Check (Defense in Depth)
    # os.path.commonpath guarantees the target is genuinely a child of UPLOAD_DIR
    if os.path.commonpath([UPLOAD_DIR, real_path]) != UPLOAD_DIR:
        return jsonify({"error": "Path traversal attempt detected"}), 403

    f.save(real_path)
    return jsonify({
        "message": "File uploaded successfully",
        "filename": filename
    }), 200

@app.route("/files/<name>")
def files(name):
    # send_from_directory inherently prevents path traversal on the read side
    return send_from_directory(UPLOAD_DIR, name)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
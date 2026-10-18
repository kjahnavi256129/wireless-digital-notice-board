
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3

app = Flask(__name__)
DB = "users.db"

def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

@app.route("/")
def home():
    return jsonify({"message": "Notice Board Backend is running!"})

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if len(username) < 3 or len(password) < 6:
        return jsonify({
            "message": "Username 3+ characters, password 6+ characters undali."
        }), 400

    try:
        with sqlite3.connect(DB) as con:
            con.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )
        return jsonify({"message": "Account created successfully!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"message": "Username already exists."}), 409

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    with sqlite3.connect(DB) as con:
        user = con.execute(
            "SELECT password FROM users WHERE username = ?",
            (username,)
        ).fetchone()

    if user and check_password_hash(user[0], password):
        return jsonify({"message": "Login successful!"})

    return jsonify({"message": "Invalid username or password."}), 401

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

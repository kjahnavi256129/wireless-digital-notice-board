 
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
import psycopg2

app = Flask(__name__)

def get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def init_db():
    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            """)

@app.route("/")
def home():
    return jsonify({"message": "Notice Board Backend is running!"})

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if len(username) < 3 or len(password) < 6:
        return jsonify({
            "message": "Username 3+ characters, password 6+ characters undali."
        }), 400

    try:
        with get_db() as con:
            with con.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                    (username, generate_password_hash(password))
                )
        return jsonify({"message": "Account created successfully!"}), 201
    except psycopg2.IntegrityError:
        return jsonify({"message": "Username already exists."}), 409

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT password FROM users WHERE username = %s",
                (username,)
            )
            user = cur.fetchone()

    if user and check_password_hash(user[0], password):
        return jsonify({"message": "Login successful!"})

    return jsonify({"message": "Invalid username or password."}), 401

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

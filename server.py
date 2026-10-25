from flask import Flask, request, jsonify, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta, timezone
import os
import psycopg2
import jwt

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")

CORS(app, origins=[
    "https://wireless-notice-board.onrender.com"
])

def get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def create_tables():
    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notices (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL,
                    notice_text TEXT NOT NULL,
                    scheduled_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

def create_token(username):
    now = datetime.now(timezone.utc)
    return jwt.encode({
        "sub": username,
        "iat": now,
        "exp": now + timedelta(hours=12)
    }, SECRET_KEY, algorithm="HS256")

def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        parts = header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"message": "Please log in again."}), 401

        try:
            payload = jwt.decode(
                parts[1],
                SECRET_KEY,
                algorithms=["HS256"]
            )
            g.username = payload["sub"]
        except (jwt.InvalidTokenError, KeyError):
            return jsonify({
                "message": "Session expired. Please log in again."
            }), 401

        return func(*args, **kwargs)
    return wrapper

@app.route("/")
def home():
    return jsonify({"message": "Notice Board Backend is running!"})

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"message": "Invalid input."}), 400

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
    except psycopg2.Error:
        app.logger.exception("Registration database error")
        return jsonify({"message": "Database error."}), 500

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"message": "Invalid input."}), 400

    username = username.strip()

    try:
        with get_db() as con:
            with con.cursor() as cur:
                cur.execute(
                    "SELECT password FROM users WHERE username = %s",
                    (username,)
                )
                user = cur.fetchone()

        if not user or not check_password_hash(user[0], password):
            return jsonify({
                "message": "Invalid username or password."
            }), 401

        return jsonify({
            "message": "Login successful!",
            "token": create_token(username),
            "username": username
        })

    except psycopg2.Error:
        app.logger.exception("Login database error")
        return jsonify({"message": "Database error."}), 500

@app.route("/notices", methods=["GET"])
@require_auth
def get_notices():
    try:
        with get_db() as con:
            with con.cursor() as cur:
                cur.execute("""
                    SELECT id, notice_text, scheduled_at, created_at
                    FROM notices
                    WHERE username = %s
                    ORDER BY created_at DESC
                """, (g.username,))
                rows = cur.fetchall()

        return jsonify([
            {
                "id": row[0],
                "notice": row[1],
                "scheduled_at": row[2].isoformat() if row[2] else None,
                "created_at": row[3].isoformat() if row[3] else None
            }
            for row in rows
        ])

    except psycopg2.Error:
        app.logger.exception("Notice retrieval error")
        return jsonify({"message": "Could not retrieve notices."}), 500

@app.route("/notices", methods=["POST"])
@require_auth
def save_notice():
    data = request.get_json(silent=True) or {}
    notice_text = data.get("notice", "")
    scheduled_at = data.get("scheduled_at") or None

    if not isinstance(notice_text, str) or not notice_text.strip():
        return jsonify({"message": "Notice is required."}), 400

    if scheduled_at is not None and not isinstance(scheduled_at, str):
        return jsonify({"message": "Invalid scheduled date."}), 400

    if len(notice_text.strip()) > 2000:
        return jsonify({"message": "Notice is too long."}), 400

    try:
        with get_db() as con:
            with con.cursor() as cur:
                cur.execute("""
                    INSERT INTO notices (username, notice_text, scheduled_at)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (g.username, notice_text.strip(), scheduled_at))
                notice_id = cur.fetchone()[0]

        return jsonify({
            "message": "Notice saved successfully!",
            "id": notice_id
        }), 201

    except (psycopg2.Error, ValueError):
        app.logger.exception("Notice save error")
        return jsonify({"message": "Could not save notice."}), 500

create_tables()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )

 
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
import psycopg2

app = Flask(__name__)

CORS(app, origins=[
    "https://wireless-notice-board.onrender.com"
])


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
    return jsonify({
        "message": "Notice Board Backend is running!"
    })


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

        return jsonify({
            "message": "Account created successfully!"
        }), 201

    except psycopg2.IntegrityError:
        return jsonify({
            "message": "Username already exists."
        }), 409

    except psycopg2.Error:
        app.logger.exception("Database registration error")
        return jsonify({
            "message": "Database error. Please try again."
        }), 500


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    try:
        with get_db() as con:
            with con.cursor() as cur:
                cur.execute(
                    "SELECT password FROM users WHERE username = %s",
                    (username,)
                )
                user = cur.fetchone()

        if user and check_password_hash(user[0], password):
            return jsonify({
                "message": "Login successful!"
            })

        return jsonify({
            "message": "Invalid username or password."
        }), 401

    except psycopg2.Error:
        app.logger.exception("Database login error")
        return jsonify({
            "message": "Database error. Please try again."
        }), 500


# Initialize database when Gunicorn loads the application.
init_db()

@app.route("/notices", methods=["GET"])
def get_notices():
    username = request.args.get("username", "").strip()

    if not username:
        return jsonify({"message": "Username required."}), 400

    try:
        with get_db() as con:
            with con.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS notices (
                        id SERIAL PRIMARY KEY,
                        username TEXT NOT NULL,
                        notice_text TEXT NOT NULL,
                        scheduled_at TIMESTAMP NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    SELECT id, notice_text, scheduled_at, created_at
                    FROM notices
                    WHERE username = %s
                    ORDER BY created_at DESC
                """, (username,))
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
        app.logger.exception("Database notice retrieval error")
        return jsonify({"message": "Could not retrieve notices."}), 500


@app.route("/notices", methods=["POST"])
def save_notice():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    notice_text = data.get("notice", "").strip()
    scheduled_at = data.get("scheduled_at") or None

    if not username or not notice_text:
        return jsonify({"message": "Username and notice are required."}), 400

    try:
        with get_db() as con:
            with con.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS notices (
                        id SERIAL PRIMARY KEY,
                        username TEXT NOT NULL,
                        notice_text TEXT NOT NULL,
                        scheduled_at TIMESTAMP NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    INSERT INTO notices (username, notice_text, scheduled_at)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (username, notice_text, scheduled_at))
                notice_id = cur.fetchone()[0]

        return jsonify({
            "message": "Notice saved successfully!",
            "id": notice_id
        }), 201

    except (psycopg2.Error, ValueError):
        app.logger.exception("Database notice save error")
        return jsonify({"message": "Could not save notice."}), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )

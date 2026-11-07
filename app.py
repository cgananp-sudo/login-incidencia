import sqlite3
import time
import hashlib
import logging
from flask import Flask, request, jsonify

@app.route("/login", methods=["POST"])
def login():
    global failed_attempts
    data = request.get_json()
    username, password = data.get("username"), data.get("password")

    if failed_attempts >= 3:
        return jsonify({"error": "Demasiados intentos fallidos. Intente más tarde."}), 429

    try:
        user = find_user(username)
    except Exception:
        # Falla del servicio: no es culpa del usuario ni cuenta como intento fallido
        auth_service.error("Error validating user token")
        auth_controller.warning(f"Login attempt failed for user: {username}")
        return jsonify({"error": "Servicio no disponible. Intente nuevamente en unos minutos."}), 503

    if user and user[1] == hash_pw(password):
        failed_attempts = 0
        return jsonify({"message": "Login exitoso"}), 200

    failed_attempts += 1
    return jsonify({"error": "Error: credenciales no válidas. Inténtelo nuevamente."}), 401

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = sqlite3.connect(DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)"
    )
    if not conn.execute("SELECT 1 FROM users").fetchone():
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("jgarcia", hash_pw("Clave123")),
        )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)"
    )
    conn.commit()
    conn.close()


def find_user(username):
    conn = sqlite3.connect(DB)
    # Simula que, sin índice, la consulta a "users" se demora y hace timeout
    has_index = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='index' AND name='idx_users_username'"
    ).fetchone()
    if not has_index:
        time.sleep(7)
        db_log.error('Timeout while querying table "users"')
        conn.close()
        raise TimeoutError("DB timeout")
    row = conn.execute(
        "SELECT username, password FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return row


@app.route("/login", methods=["POST"])
def login():
    global failed_attempts
    data = request.get_json()
    username, password = data.get("username"), data.get("password")

    if failed_attempts >= 3:
        return jsonify({"error": "Internal Server Error"}), 500

    try:
        user = find_user(username)
        if user and user[1] == hash_pw(password):
            failed_attempts = 0
            return jsonify({"message": "Login exitoso"}), 200
        failed_attempts += 1
        return jsonify({"error": "Error: credenciales no válidas. Inténtelo nuevamente."}), 401
    except Exception:
        # BUG: cualquier falla interna se reporta como credenciales inválidas
        auth_service.error("Error validating user token")
        auth_controller.warning(f"Login attempt failed for user: {username}")
        failed_attempts += 1
        return jsonify({"error": "Error: credenciales no válidas. Inténtelo nuevamente."}), 401


if __name__ == "__main__":
    init_db()
    app.run(port=5000)
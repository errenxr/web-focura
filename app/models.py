import mysql.connector
import bcrypt
from flask import current_app


def get_db_connection():
    return mysql.connector.connect(
        host=current_app.config["DB_HOST"],
        user=current_app.config["DB_USER"],
        password=current_app.config["DB_PASSWORD"],
        database=current_app.config["DB_NAME"]
    )


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_user(email, password, nama_anak, umur):
    conn = get_db_connection()
    cursor = conn.cursor()

    password_hash = hash_password(password)

    query = """
    INSERT INTO users (email, password_hash, nama_anak, umur)
    VALUES (%s, %s, %s, %s)
    """

    cursor.execute(query, (email, password_hash, nama_anak, umur))
    conn.commit()

    cursor.close()
    conn.close()


def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user


def verify_user(email, password):
    user = get_user_by_email(email)

    if user and check_password(password, user["password_hash"]):
        return user

    return None


def create_session(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sessions (user_id, start_time, status)
        VALUES (%s, NOW(), 'aktif')
    """, (user_id,))

    conn.commit()
    session_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return session_id


def end_session(session_id, skor_total):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    UPDATE sessions
    SET end_time = NOW(),
        durasi_total = TIMESTAMPDIFF(SECOND, start_time, NOW()),
        skor_total = %s,
        status = 'selesai'
    WHERE id = %s
    """

    cursor.execute(query, (skor_total, session_id))
    conn.commit()

    cursor.close()
    conn.close()


def get_user_sessions(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM sessions WHERE user_id = %s", (user_id,))
    sessions = cursor.fetchall()

    cursor.close()
    conn.close()

    return sessions
import mysql.connector
import bcrypt
from flask import current_app


# ================= DATABASE =================
def get_db_connection():
    return mysql.connector.connect(
        host=current_app.config["DB_HOST"],
        user=current_app.config["DB_USER"],
        password=current_app.config["DB_PASSWORD"],
        database=current_app.config["DB_NAME"]
    )


# ================= PASSWORD =================
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# ================= USER (ORANG TUA) =================
def create_user(email, password):
    conn = get_db_connection()
    cursor = conn.cursor()

    password_hash = hash_password(password)

    query = """
    INSERT INTO users (email, password_hash)
    VALUES (%s, %s)
    """

    cursor.execute(query, (email, password_hash))
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


def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user


def verify_user(email, password):
    user = get_user_by_email(email)

    if user and check_password(password, user["password_hash"]):
        return user

    return None


# ================= ANAK =================
def create_anak(user_id, nama_anak, umur):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO anak (user_id, nama_anak, umur, current_level)
    VALUES (%s, %s, %s, 'mudah')
    """

    cursor.execute(query, (user_id, nama_anak, umur))
    conn.commit()

    cursor.close()
    conn.close()


def get_anak_by_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM anak WHERE user_id = %s", (user_id,))
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data


def get_anak_by_id(anak_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM anak WHERE id = %s", (anak_id,))
    data = cursor.fetchone()

    cursor.close()
    conn.close()

    return data


# 🔥 OPTIONAL (untuk masa depan Q-Learning / manual update)
def update_level_anak(anak_id, level):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE anak
        SET current_level = %s
        WHERE id = %s
    """, (level, anak_id))

    conn.commit()
    cursor.close()
    conn.close()


# ================= SESSION (BERDASARKAN ANAK) =================
def create_session(anak_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sessions (anak_id, start_time, status)
        VALUES (%s, NOW(), 'aktif')
    """, (anak_id,))

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


def get_sessions_by_anak(anak_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        id,
        DATE(start_time) AS tanggal,
        durasi_total,
        skor_total,
        status
    FROM sessions
    WHERE anak_id = %s
    ORDER BY start_time DESC
    """

    cursor.execute(query, (anak_id,))
    sessions = cursor.fetchall()

    cursor.close()
    conn.close()

    return sessions

def update_anak(anak_id, nama_anak, umur):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE anak SET nama_anak=%s, umur=%s WHERE id=%s",
        (nama_anak, umur, anak_id)
    )
    conn.commit()
    conn.close()


def delete_anak(anak_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # hapus dulu session (jika ada foreign key)
    cursor.execute("DELETE FROM sessions WHERE anak_id=%s", (anak_id,))
    cursor.execute("DELETE FROM anak WHERE id=%s", (anak_id,))

    conn.commit()
    conn.close()
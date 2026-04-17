from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from .models import create_user, verify_user, get_user_sessions, create_session, end_session

ACTIVE_USER = None

main = Blueprint('main', __name__)


@main.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return "Email dan password harus diisi!"

        user = verify_user(email, password)

        if user:
            session["user_id"] = user["id"]
            session["nama_anak"] = user["nama_anak"]

            global ACTIVE_USER
            ACTIVE_USER = user
            return redirect(url_for("main.dashboard"))
        else:
            return "Login gagal!"

    return render_template("login.html")


@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        nama_anak = request.form.get("nama_anak")
        umur = request.form.get("umur")

        if not email or not password or not nama_anak or not umur:
            return "Semua field harus diisi!"

        create_user(email, password, nama_anak, umur)

        return redirect(url_for("main.login"))

    return render_template("registrasi.html")


@main.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    user_id = session["user_id"]
    nama_anak = session["nama_anak"]

    sessions = get_user_sessions(user_id)

    total_sesi = len(sessions)
    total_skor = sum(s["skor_total"] or 0 for s in sessions)

    return render_template(
        "dashboard.html",
        nama_anak=nama_anak,
        total_sesi=total_sesi,
        total_skor=total_skor
    )

@main.route("/progress")
def progress():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    user_id = session["user_id"]

    sessions = get_user_sessions(user_id)

    return render_template(
        "progress.html",
        sessions=sessions
    )


@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))


# ================= API =================
@main.route("/api/start_session", methods=["POST"])
def api_start_session():
    user_id = request.json.get("user_id")
    session_id = create_session(user_id)
    return jsonify({"session_id": session_id})


@main.route("/api/end_session", methods=["POST"])
def api_end_session():
    session_id = request.json.get("session_id")
    skor = request.json.get("skor")

    end_session(session_id, skor)

    return jsonify({"status": "success"})

@main.route("/api/get_active_user", methods=["GET"])
def get_active_user():
    global ACTIVE_USER

    if ACTIVE_USER:
        return jsonify({
            "status": "success",
            "user": ACTIVE_USER
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Tidak ada user aktif"
        })
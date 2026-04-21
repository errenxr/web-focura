from flask import Blueprint, flash, render_template, request, redirect, url_for, session, jsonify
from .models import create_anak, create_user, get_user_by_id, verify_user, get_anak_by_user, get_anak_by_id, create_session, end_session, get_sessions_by_anak, update_anak, delete_anak


main = Blueprint('main', __name__)


@main.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Validasi field kosong
        if not email or not password:
            return render_template(
                "login.html",
                error="Email dan password harus diisi!",
                form_email=email
            )

        user = verify_user(email, password)

        if user:
            session["user_id"] = user["id"]
            session["email"] = user["email"]

            return redirect(url_for("main.dashboard_parent"))
        else:
            return render_template(
                "login.html",
                error="Email atau password yang Anda masukkan salah.",
                form_email=email
            )

    return render_template("login.html", error=None, form_email="")


@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return render_template(
                "registrasi.html",
                error="Email dan password harus diisi!",
                form_data={"email": email}
            )

        create_user(email, password)

        return redirect(url_for("main.login"))

    return render_template("registrasi.html", error=None, form_data={})


@main.route("/dashboard_parent")
def dashboard_parent():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    user_id = session["user_id"]

    anak_list = get_anak_by_user(user_id)

    return render_template(
        "dashboard_parent.html",
        nama_ortu=session.get("email"),  # bisa diganti nanti
        anak_list=anak_list,
        jumlah_anak=len(anak_list),
        active_page="dashboard_parent"
    )

@main.route("/daftar_anak")
def daftar_anak():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    user_id = session["user_id"]
    anak_list = get_anak_by_user(user_id)

    return render_template(
        "anak.html",
        anak_list=anak_list,
        nama_ortu=session.get("email"),
        active_page="anak"
    )


@main.route("/register_anak", methods=["POST"])
def register_anak():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    user_id = session["user_id"]
    nama_anak = request.form.get("nama_anak")
    umur = request.form.get("umur")

    if not nama_anak or not umur:
        return "Semua field harus diisi!"

    try:
        umur = int(umur)
    except:
        return "Umur harus angka!"

    if umur < 5 or umur > 7:
        return "Umur anak harus antara 5 sampai 7 tahun!"

    create_anak(user_id, nama_anak, umur)
    flash(f"Anak '{nama_anak}' berhasil didaftarkan! 🎉", "success")
    return redirect(url_for("main.daftar_anak"))

@main.route("/edit_anak/<int:anak_id>", methods=["POST"])
def edit_anak(anak_id):
    anak = get_anak_by_id(anak_id)
    if not anak or anak["user_id"] != session["user_id"]:
        return "Akses tidak diizinkan!"
    
    if "user_id" not in session:
        return redirect(url_for("main.login"))
 
    nama_anak = request.form.get("nama_anak")
    umur      = request.form.get("umur")
 
    if not nama_anak or not umur:
        flash("Semua field harus diisi!", "error")
        return redirect(url_for("main.daftar_anak"))
 
    try:
        umur = int(umur)
    except ValueError:
        flash("Umur harus berupa angka!", "error")
        return redirect(url_for("main.daftar_anak"))
 
    if umur < 5 or umur > 7:
        flash("Usia anak harus antara 5–7 tahun!", "error")
        return redirect(url_for("main.daftar_anak"))
 
    
    update_anak(anak_id, nama_anak, umur)
 
    flash(f"Data '{nama_anak}' berhasil diperbarui! ✏️", "success")
    return redirect(url_for("main.daftar_anak"))

@main.route("/hapus_anak/<int:anak_id>", methods=["POST"])
def hapus_anak(anak_id):
    anak = get_anak_by_id(anak_id)
    if not anak or anak["user_id"] != session["user_id"]:
        return "Akses tidak diizinkan!"
    
    if "user_id" not in session:
        return redirect(url_for("main.login"))
 
    # Ambil nama anak sebelum dihapus untuk pesan notifikasi
    anak = get_anak_by_id(anak_id)
    nama = anak["nama_anak"] if anak else "Anak"
 
    delete_anak(anak_id)
 
    flash(f"Data '{nama}' berhasil dihapus.", "success")
    return redirect(url_for("main.daftar_anak"))

@main.route("/dashboard_anak/<int:anak_id>")
def dashboard_anak(anak_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    user_id = session["user_id"]

    anak = get_anak_by_id(anak_id)

    if not anak or anak["user_id"] != user_id:
        return "Akses tidak diizinkan!"

    session["anak_id"] = anak["id"]
    session["nama_anak"] = anak["nama_anak"]
    session["umur"] = anak["umur"]

    sessions = get_sessions_by_anak(anak_id)

    total_sesi = len(sessions)
    total_skor = sum(s["skor_total"] or 0 for s in sessions)

    return render_template(
        "dashboard.html",
        nama_anak=anak["nama_anak"],
        umur_anak=anak["umur"],
        total_sesi=total_sesi,
        total_skor=total_skor,
        anak_id=anak_id,
        active_page="dashboard"
    )


@main.route("/progress/<int:anak_id>")
def progress_anak(anak_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    user_id = session["user_id"]
    anak = get_anak_by_id(anak_id)

    if not anak or anak["user_id"] != user_id:
        return "Akses tidak diizinkan!"

    sessions = get_sessions_by_anak(anak_id)

    return render_template(
        "progress.html",
        sessions=sessions,
        active_page="progress"
    )


@main.route("/user")
def user_profile():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    # Pastikan anak sudah dipilih
    if "anak_id" not in session:
        return redirect(url_for("main.dashboard_parent"))

    anak_id = session["anak_id"]
    anak = get_anak_by_id(anak_id)

    if not anak:
        return "Data anak tidak ditemukan!"

    return render_template(
        "user.html",
        anak=anak,
        nama_anak=anak["nama_anak"],
        umur_anak=anak["umur"],
        active_page="user"
    )

@main.route("/pilih_anak/<int:anak_id>")
def pilih_anak(anak_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    user_id = session["user_id"]
    anak = get_anak_by_id(anak_id)

    if not anak or anak["user_id"] != user_id:
        return "Akses tidak diizinkan!"

    session["anak_id"] = anak["id"]
    session["nama_anak"] = anak["nama_anak"]
    session["umur"] = anak["umur"]

    return redirect(url_for("main.dashboard_anak", anak_id=anak_id))

@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))


# ================= API =================
@main.route("/api/start_session", methods=["POST"])
def api_start_session():
    anak_id = request.json.get("anak_id")
    session_id = create_session(anak_id)

    return jsonify({"session_id": session_id})


@main.route("/api/end_session", methods=["POST"])
def api_end_session():
    session_id = request.json.get("session_id")
    skor = request.json.get("skor")
    end_session(session_id, skor)
    return jsonify({"status": "success"})


@main.route("/api/get_active_user", methods=["GET"])
def get_active_user():
    if "anak_id" in session:
        return jsonify({
            "status": "success",
            "user": {
                "id": session["anak_id"],
                "nama_anak": session["nama_anak"],
                "umur": session["umur"]
            }
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Tidak ada anak aktif"
        })
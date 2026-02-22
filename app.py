from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from datetime import datetime, timedelta
import uuid
import os
import base64
from face_matcher import find_student
from database import *

app = Flask(__name__)
app.secret_key = "supersecretkey"

init_db()

os.makedirs("dataset/students", exist_ok=True)
os.makedirs("temp", exist_ok=True)

session_data = {
    "active": False,
    "subject": None,
    "end_time": None,
    "session_id": None
}

# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")


# ---------- ADMIN LOGIN ----------
@app.route("/admin", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect("/admin/dashboard")
        else:
            return render_template("admin_login.html", error="Invalid Credentials")

    return render_template("admin_login.html")


# ---------- ADMIN DASHBOARD ----------
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    return render_template("admin_dashboard.html")


# ---------- ADMIN LOGOUT ----------
@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/")

# ---------- TEACHER LOGIN ----------
@app.route("/teacher", methods=["GET","POST"])
def teacher():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "teacher1" and password == "123":
            session["teacher"] = "Artificial Intelligence"
            return redirect("/teacher/dashboard")

        elif username == "teacher2" and password == "123":
            session["teacher"] = "DBMS"
            return redirect("/teacher/dashboard")

        else:
            return render_template("teacher_login.html", error="Invalid Login")

    return render_template("teacher_login.html")


# ---------- TEACHER DASHBOARD ----------
@app.route("/teacher/dashboard", methods=["GET","POST"])
def teacher_dashboard():
    if not session.get("teacher"):
        return redirect("/teacher")

    subject = session["teacher"]

    if request.method == "POST" and not session_data["active"]:
        session_data["active"] = True
        session_data["subject"] = subject
        session_data["end_time"] = datetime.now() + timedelta(minutes=5)
        session_data["session_id"] = str(uuid.uuid4())[:8]

    time_left = None
    scan_link = None

    if session_data["active"]:
        if datetime.now() > session_data["end_time"]:
            session_data["active"] = False
        else:
            remaining = session_data["end_time"] - datetime.now()
            time_left = str(remaining).split(".")[0]

            # 🔥 IMPORTANT CHANGE FOR PUBLIC LINK
            base_url = request.host_url.rstrip("/")
            scan_link = f"{base_url}/scan?session={session_data['session_id']}"

    return render_template(
        "teacher_dashboard.html",
        subject=subject,
        session_active=session_data["active"],
        time_left=time_left,
        scan_link=scan_link
    )


# ---------- TEACHER LOGOUT ----------
@app.route("/teacher/logout")
def teacher_logout():
    session.pop("teacher", None)
    return redirect("/")

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        roll = request.form["roll"]
        image_data = request.form["image"]

        add_student(name, roll, "ALL")

        if image_data:
            img_str = image_data.split(",")[1]
            img_bytes = base64.b64decode(img_str)

            folder = f"dataset/students/{roll}_{name}"
            os.makedirs(folder, exist_ok=True)

            filename = f"{folder}/{len(os.listdir(folder))+1}.png"

            with open(filename, "wb") as f:
                f.write(img_bytes)

        return "Student Registered Successfully!"

    return render_template("register.html")


# ---------- STUDENTS ----------
@app.route("/students")
def students():
    if not session.get("admin"):
        return redirect("/admin")

    students = get_all_students()
    return render_template("students.html", students=students)


@app.route("/student/<roll>")
def student_profile(roll):
    if not session.get("admin"):
        return redirect("/admin")

    student = get_student(roll)

    folder = f"dataset/students/{roll}_{student[1]}"
    images = []

    if os.path.exists(folder):
        for f in os.listdir(folder):
            images.append("/dataset/" + folder.split("dataset/")[1] + "/" + f)

    return render_template(
        "student_profile.html",
        student=student,
        images=images
    )


@app.route('/dataset/<path:filename>')
def dataset_files(filename):
    return send_from_directory('dataset', filename)


# ---------- ADMIN ATTENDANCE ----------
@app.route("/admin_attendance")
def admin_attendance():
    if not session.get("admin"):
        return redirect("/admin")

    records = get_all_attendance()
    return render_template("attendance_table.html", records=records)


# ---------- SUBJECTS ----------
@app.route("/subjects")
def subjects():
    if not session.get("admin"):
        return redirect("/admin")

    return render_template("subjects.html")


@app.route("/subject/<subject>")
def subject_view(subject):
    if not session.get("admin"):
        return redirect("/admin")

    records = get_subject_attendance(subject)
    return render_template(
        "subject_attendance.html",
        records=records,
        subject=subject
    )


# ---------- QR ----------
@app.route("/qr", methods=["GET", "POST"])
def qr():
    msg = None
    if request.method == "POST":
        name = request.form["name"]
        roll = request.form["roll"]
        msg = mark_entry_exit(name, roll)

    return render_template("qr_scan.html", msg=msg)


# ---------- SCAN ----------
@app.route("/scan")
def scan():
    session_id = request.args.get("session")

    if not session_data["active"]:
        return "Session Closed"

    if session_id != session_data["session_id"]:
        return "Invalid Session"

    return render_template("scan.html")


@app.route("/process_scan", methods=["POST"])
def process_scan():
    if not session_data["active"]:
        return "Session Closed"

    data = request.get_json()
    image_data = data["image"]

    img_str = image_data.split(",")[1]
    img_bytes = base64.b64decode(img_str)

    temp_path = "temp/capture.png"
    with open(temp_path, "wb") as f:
        f.write(img_bytes)

    student = find_student(temp_path)

    if student:
        name = student.split(" (")[0]
        roll = student.split("(")[1].replace(")", "")
        subject = session_data["subject"]
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        saved = mark_attendance(name, roll, subject, time)

        if saved:
            return f"Attendance Marked for {student}"
        else:
            return f"{student} already marked present"

    return "Face Not Recognized"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
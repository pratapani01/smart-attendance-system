import sqlite3

DB_NAME = "attendance.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Students table
    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        roll TEXT UNIQUE,
        subject TEXT
    )
    """)

    # Attendance table
    c.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        roll TEXT,
        subject TEXT,
        time TEXT,
        marked_by TEXT,
        reason TEXT
    )
    """)

    # Gate logs
    c.execute("""
    CREATE TABLE IF NOT EXISTS entry_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        roll TEXT,
        entry_time TEXT,
        exit_time TEXT
    )
    """)

    conn.commit()
    conn.close()


# ---------- STUDENT FUNCTIONS ----------

def add_student(name, roll, subject):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO students (name, roll, subject) VALUES (?,?,?)",
              (name, roll, subject))
    conn.commit()
    conn.close()

def get_all_students():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return rows

def get_student(roll):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE roll=?", (roll,))
    row = c.fetchone()
    conn.close()
    return row


# ---------- ATTENDANCE FUNCTIONS ----------

def mark_attendance(name, roll, subject, time, marked_by="AI", reason=""):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT * FROM attendance 
    WHERE roll=? AND subject=? AND date(time)=date(?)
    """, (roll, subject, time))

    if c.fetchone():
        conn.close()
        return False

    c.execute("""
    INSERT INTO attendance (name, roll, subject, time, marked_by, reason)
    VALUES (?,?,?,?,?,?)
    """, (name, roll, subject, time, marked_by, reason))

    conn.commit()
    conn.close()
    return True

def get_all_attendance():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM attendance ORDER BY time DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_subject_attendance(subject):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM attendance WHERE subject=? ORDER BY time DESC", (subject,))
    rows = c.fetchall()
    conn.close()
    return rows


# ---------- GATE FUNCTIONS ----------

def mark_entry_exit(name, roll):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT id FROM entry_logs 
    WHERE roll=? AND exit_time IS NULL
    """, (roll,))
    row = c.fetchone()

    now = sqlite3.datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if row:
        c.execute("UPDATE entry_logs SET exit_time=? WHERE id=?", (now, row[0]))
        conn.commit()
        conn.close()
        return "Exit Marked"
    else:
        c.execute("""
        INSERT INTO entry_logs (name, roll, entry_time, exit_time)
        VALUES (?,?,?,NULL)
        """, (name, roll, now))
        conn.commit()
        conn.close()
        return "Entry Marked"

def get_entry_logs():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM entry_logs ORDER BY entry_time DESC")
    rows = c.fetchall()
    conn.close()
    return rows
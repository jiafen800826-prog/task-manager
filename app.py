import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session

# --- Flask Setup ---
app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_FILE = "tasks.db"

# --- DB Helper ---
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# --- Initialize DB ---
def init_db():
    conn = get_db_connection()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        due_date TEXT,
        priority TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    conn.commit()
    conn.close()

init_db()

# --- Routes ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        
        if user:
            if check_password_hash(user["password"], password):
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                conn.close()
                return redirect(url_for("index"))
            else:
                conn.close()
                return "Incorrect password"
        else:
            # Auto-register
            hashed_pw = generate_password_hash(password)
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
            user_id = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()["id"]
            session["user_id"] = user_id
            session["username"] = username
            conn.close()
            return redirect(url_for("index"))
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    filter_type = request.args.get("filter")
    
    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    
    # Filter
    if filter_type == "active":
        tasks = [t for t in tasks if not t["completed"]]
    elif filter_type == "completed":
        tasks = [t for t in tasks if t["completed"]]
    
    return render_template("index.html", tasks=tasks, username=session["username"])

@app.route("/add", methods=["POST"])
def add_task():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    title = request.form["title"]
    due_date = request.form.get("due_date")
    priority = request.form.get("priority")
    user_id = session["user_id"]
    
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO tasks (user_id, title, due_date, priority) VALUES (?, ?, ?, ?)",
        (user_id, title, due_date, priority)
    )
    conn.commit()
    conn.close()
    
    return redirect(url_for("index"))

@app.route("/toggle/<int:task_id>")
def toggle_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    task = conn.execute("SELECT completed FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if task:
        new_status = 0 if task["completed"] else 1
        conn.execute("UPDATE tasks SET completed = ? WHERE id = ?", (new_status, task_id))
        conn.commit()
    conn.close()
    
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run()






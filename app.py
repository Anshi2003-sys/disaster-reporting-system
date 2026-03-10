from flask import Flask, render_template, request, redirect, url_for,session
import sqlite3

app = Flask(__name__)
app.secret_key = "disaster_secret_key"

DATABASE = "database.db"


# ---------------- DATABASE CONNECTION ----------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- CREATE TABLES ----------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)

    # DISASTER TYPES TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS disasters (
        disaster_id INTEGER PRIMARY KEY AUTOINCREMENT,
        disaster_name TEXT NOT NULL
    )
    """)

    # REPORTS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        disaster_id INTEGER,
        location TEXT,
        description TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (disaster_id) REFERENCES disasters(disaster_id)
    )
    """)

    conn.commit()

    # Insert disaster types if table empty
    cursor.execute("SELECT COUNT(*) FROM disasters")
    count = cursor.fetchone()[0]

    if count == 0:
        disasters = [("Flood",), ("Earthquake",), ("Fire",), ("Landslide",)]
        cursor.executemany("INSERT INTO disasters (disaster_name) VALUES (?)", disasters)

    conn.commit()
    conn.close()


# Run database initialization
init_db()


# ---------------- HOME PAGE ----------------
@app.route("/")
def home():

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row

    reports = conn.execute("""
        SELECT users.name, disasters.disaster_name, reports.location
        FROM reports
        JOIN users ON reports.user_id = users.user_id
        JOIN disasters ON reports.disaster_id = disasters.disaster_id
        ORDER BY reports.report_id DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return render_template("index.html", reports=reports)


# ---------------- REPORT DISASTER ----------------
@app.route("/report", methods=["GET", "POST"])
def report():

    conn = get_db_connection()

    disasters = conn.execute("SELECT * FROM disasters").fetchall()

    if request.method == "POST":

        name = request.form["name"]
        location = request.form["location"]
        disaster = request.form["disaster"]
        description = request.form["description"]
        latitude = request.form["latitude"]
        longitude = request.form["longitude"]

        # Insert user
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
        user_id = cursor.lastrowid

        # Get disaster id
        cursor.execute(
            "SELECT disaster_id FROM disasters WHERE disaster_name=?",
            (disaster,)
        )
        disaster_id = cursor.fetchone()[0]

        # Insert report
        cursor.execute("""
            INSERT INTO reports (user_id, disaster_id, location, description,latitude, longitude)
            VALUES (?, ?, ?, ?,?,?)
        """, (user_id, disaster_id, location, description,latitude, longitude))

        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    conn.close()

    return render_template("report.html", disasters=disasters)


# ---------------- ALERTS PAGE ----------------
@app.route("/alerts")
def alerts():
    return render_template("alerts.html")


# ---------------- MAP PAGE ----------------
@app.route("/map")
def map_page():

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT reports.report_id,
               users.name,
               disasters.disaster_name,
               reports.location,
               reports.description,
               reports.latitude,
               reports.longitude
        FROM reports
        JOIN users ON reports.user_id = users.user_id
        JOIN disasters ON reports.disaster_id = disasters.disaster_id
    """).fetchall()

    conn.close()
    
    reports = [dict(row) for row in rows]
    return render_template("map.html", reports=reports)


# ---------------- ADMIN LOGIN ----------------
@app.route("/admin_login", methods=["GET","POST"])
def admin_login():

    if request.method == "POST":

        admin_id = request.form["admin_id"]
        password = request.form["password"]

        if admin_id == "admin" and password == "1234":
            session["admin"] = True
            return redirect(url_for("admin"))

        else:
            return "Invalid Admin Credentials"

    return render_template("admin_login.html")

# ---------------- ADMIN LOGOUT ----------------
@app.route("/logout")
def logout():

    session.pop("admin", None)
    return redirect(url_for("admin_login"))

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect(url_for("admin_login"))
    
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row

    reports = conn.execute("""
        SELECT reports.report_id, users.name, disasters.disaster_name,
               reports.location, reports.description
        FROM reports
        JOIN users ON reports.user_id = users.user_id
        JOIN disasters ON reports.disaster_id = disasters.disaster_id
        ORDER BY reports.report_id DESC
    """).fetchall()

    conn.close()

    return render_template("admin.html", reports=reports)

# ---------------- DELETE REPORT ----------------
@app.route("/delete/<int:id>")
def delete(id):

    conn = sqlite3.connect("database.db")
    conn.execute("DELETE FROM reports WHERE report_id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
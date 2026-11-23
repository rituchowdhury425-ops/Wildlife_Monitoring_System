
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from functools import wraps
from pathlib import Path
from datetime import datetime
import sqlite3

auth = Blueprint("auth", __name__)

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "wildlife.db"


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# Check whether a user is logged in.
def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))

        return view(*args, **kwargs)

    return wrapped_view


# Check whether a user is an administrator.
def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))

        if session.get("role") != "admin":
            flash("Administrator access required.", "danger")
            return redirect(url_for("home"))

        return view(*args, **kwargs)

    return wrapped_view


# USER REGISTRATION
@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please complete all required fields.", "danger")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        connection = get_db()

        try:
            # Prevent two simultaneous registrations from
            # incorrectly creating two first administrators.
            connection.execute("BEGIN IMMEDIATE")

            existing_user = connection.execute(
                "SELECT id FROM users WHERE email = ?",
                (email,)
            ).fetchone()

            if existing_user:
                connection.rollback()
                flash("An account with this email already exists.", "danger")
                return render_template("register.html")

            user_count = connection.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0]

            if user_count == 0:
                role = "admin"
            else:
                role = "member"

            password_hash = generate_password_hash(password)

            cursor = connection.execute("""
                INSERT INTO users
                (name, email, password_hash, role, registered_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                email,
                password_hash,
                role,
                datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
            ))

            new_user_id = cursor.lastrowid

            # Assign the old detections to the first administrator.
            if role == "admin":
                connection.execute("""
                    UPDATE detections
                    SET user_id = ?
                    WHERE user_id IS NULL
                """, (new_user_id,))

            connection.commit()

            flash(
                f"Account created successfully! Your role is {role.title()}. Please log in.",
                "success"
            )

            return redirect(url_for("auth.login"))

        except sqlite3.Error:
            connection.rollback()
            flash("A database error occurred. Please try again.", "danger")
            return render_template("register.html")

        finally:
            connection.close()

    return render_template("register.html")


# USER LOGIN
@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = get_db()

        user = connection.execute("""
            SELECT * FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        connection.close()

        if user and check_password_hash(
            user["password_hash"], password
        ):

            session.clear()

            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            flash(f"Welcome back, {user['name']}!", "success")

            return redirect(url_for("home"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


# USER LOGOUT
@auth.route("/logout")
@login_required
def logout():

    session.clear()

    flash("You have been logged out successfully.", "success")

    return redirect(url_for("auth.login"))


from flask import (
    Flask, render_template, request, send_from_directory,
    session, flash, redirect, url_for
)
from werkzeug.utils import secure_filename
from transformers import pipeline
from pathlib import Path
from datetime import datetime
from auth import auth, login_required
import sqlite3
import uuid
import math
import os
import secrets

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
DATABASE = BASE_DIR / "wildlife.db"

UPLOAD_FOLDER.mkdir(exist_ok=True)

# Persistent local secret key.
# On deployment, set WILDLIFE_SECRET_KEY as an environment variable.
SECRET_FILE = BASE_DIR / ".flask_secret_key"

if os.environ.get("WILDLIFE_SECRET_KEY"):
    app.secret_key = os.environ["WILDLIFE_SECRET_KEY"]
else:
    if not SECRET_FILE.exists():
        SECRET_FILE.write_text(secrets.token_hex(32))
    app.secret_key = SECRET_FILE.read_text().strip()

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("FLASK_HTTPS", "").lower() == "true"
)

# Register login and registration routes.
app.register_blueprint(auth)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}


# SIMULATED GPS DATA — fictional demonstration coordinates only.
gps_locations = [
    {
        "animal_id": "ANIMAL-001",
        "species": "Bengal Tiger",
        "latitude": 20.0010,
        "longitude": 80.0020,
        "movement": "Moving",
        "status": "Active"
    },
    {
        "animal_id": "ANIMAL-002",
        "species": "Asian Elephant",
        "latitude": 20.0040,
        "longitude": 80.0050,
        "movement": "Resting",
        "status": "Active"
    },
    {
        "animal_id": "ANIMAL-003",
        "species": "Spotted Deer",
        "latitude": 19.9980,
        "longitude": 80.0060,
        "movement": "Moving",
        "status": "Active"
    }
]


# DATABASE CONNECTION
def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# CREATE / CHECK DATABASE TABLES.
# Existing records are preserved.
def initialize_database():
    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_filename TEXT NOT NULL,
            predicted_species TEXT NOT NULL,
            confidence REAL NOT NULL,
            detected_at TEXT NOT NULL,
            user_id INTEGER
        )
    """)

    # Add user_id if this is an older database.
    columns = [
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(detections)"
        ).fetchall()
    ]

    if "user_id" not in columns:
        connection.execute(
            "ALTER TABLE detections ADD COLUMN user_id INTEGER"
        )

    connection.commit()
    connection.close()


initialize_database()


# LOAD PRETRAINED AI MODEL
print("Loading Wildlife AI model...")

classifier = pipeline(
    "image-classification",
    model="microsoft/resnet-50"
)

print("Wildlife AI model is ready!")


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# SAVE DETECTION WITH THE LOGGED-IN USER'S ID.
def save_detection(filename, species, confidence, user_id):
    connection = get_db()

    connection.execute("""
        INSERT INTO detections
        (image_filename, predicted_species, confidence, detected_at, user_id)
        VALUES (?, ?, ?, ?, ?)
    """, (
        filename,
        species,
        confidence,
        datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"),
        user_id
    ))

    connection.commit()
    connection.close()


def get_total_detections():
    connection = get_db()

    total = connection.execute(
        "SELECT COUNT(*) FROM detections"
    ).fetchone()[0]

    connection.close()
    return total


def get_recent_detections(limit=5):
    connection = get_db()

    records = connection.execute("""
        SELECT detections.*, users.name AS uploader_name
        FROM detections
        LEFT JOIN users ON detections.user_id = users.id
        ORDER BY detections.id DESC
        LIMIT ?
    """, (limit,)).fetchall()

    connection.close()
    return records


def get_detection_page(page, per_page=10):
    connection = get_db()

    total = connection.execute(
        "SELECT COUNT(*) FROM detections"
    ).fetchone()[0]

    total_pages = max(1, math.ceil(total / per_page))
    page = max(1, min(page, total_pages))
    offset = (page - 1) * per_page

    records = connection.execute("""
        SELECT detections.*, users.name AS uploader_name
        FROM detections
        LEFT JOIN users ON detections.user_id = users.id
        ORDER BY detections.id DESC
        LIMIT ? OFFSET ?
    """, (per_page, offset)).fetchall()

    connection.close()

    return records, total, total_pages, page


# PUBLIC MAIN HOMEPAGE.
# Visitors can view the dashboard.
# Only logged-in members can submit images for detection.
@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        if "user_id" not in session:
            flash(
                "Please register or log in to use AI animal detection.",
                "warning"
            )
            return redirect(url_for("auth.login"))

        if "animalImage" not in request.files:
            flash("No image was selected.", "danger")
            return redirect(url_for("home"))

        file = request.files["animalImage"]

        if file.filename == "":
            flash("No image was selected.", "danger")
            return redirect(url_for("home"))

        if not allowed_file(file.filename):
            flash("Unsupported image format.", "danger")
            return redirect(url_for("home"))

        original_name = secure_filename(file.filename)
        extension = original_name.rsplit(".", 1)[1].lower()

        unique_name = f"{uuid.uuid4().hex}.{extension}"
        image_path = UPLOAD_FOLDER / unique_name

        file.save(image_path)

        try:
            predictions = classifier(str(image_path), top_k=5)

            best_prediction = predictions[0]
            prediction = best_prediction["label"]
            confidence = round(
                best_prediction["score"] * 100, 2
            )

            save_detection(
                unique_name,
                prediction,
                confidence,
                session["user_id"]
            )

            flash("Animal detection completed successfully!", "success")

        except Exception:
            if image_path.exists():
                image_path.unlink()

            flash(
                "Animal detection failed. Please try another image.",
                "danger"
            )

        return redirect(url_for("home"))

    # Public visitors can see recent detections and statistics.
    history = get_recent_detections(5)
    total_history_count = get_total_detections()

    return render_template(
        "index.html",
        uploaded=None,
        prediction=None,
        confidence=None,
        predictions=[],
        history=history,
        total_history_count=total_history_count,
        gps_locations=gps_locations
    )


# PUBLIC DETECTION HISTORY.
# Everyone can view records.
@app.route("/history")
def detection_history():

    try:
        requested_page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        requested_page = 1

    records, total, total_pages, current_page = get_detection_page(
        requested_page,
        per_page=10
    )

    return render_template(
        "history.html",
        history=records,
        total=total,
        total_pages=total_pages,
        current_page=current_page
    )


# DISPLAY UPLOADED IMAGES.
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == "__main__":
    app.run(debug=True)

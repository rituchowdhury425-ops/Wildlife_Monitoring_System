
import sqlite3
from pathlib import Path

DATABASE = Path(__file__).resolve().parent / "wildlife.db"


def upgrade_database():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    try:
        cursor.execute("PRAGMA foreign_keys = ON")

        # Create users table.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'member'
                    CHECK (role IN ('admin', 'mentor', 'member')),
                registered_at TEXT NOT NULL
            )
        """)

        # Add user_id to existing detections table if missing.
        columns = [
            row[1]
            for row in cursor.execute(
                "PRAGMA table_info(detections)"
            ).fetchall()
        ]

        if "user_id" not in columns:
            cursor.execute("""
                ALTER TABLE detections
                ADD COLUMN user_id INTEGER REFERENCES users(id)
            """)

        connection.commit()

        print("DATABASE UPGRADE SUCCESSFUL!")
        print("Users table is ready.")
        print("Detection table is ready.")
        print("Existing detection records have been preserved.")

        print(
            "Existing detections:",
            cursor.execute(
                "SELECT COUNT(*) FROM detections"
            ).fetchone()[0]
        )

        print(
            "Registered users:",
            cursor.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0]
        )

        print(
            "Detection columns:",
            [
                row[1]
                for row in cursor.execute(
                    "PRAGMA table_info(detections)"
                ).fetchall()
            ]
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    upgrade_database()

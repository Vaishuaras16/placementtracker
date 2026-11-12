import sqlite3
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "placements.db"


def initialize_database(database_path=DATABASE_PATH):
    """Create the applications table and add new optional columns in place."""
    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    job_role TEXT NOT NULL,
                    application_date TEXT,
                    status TEXT,
                    follow_up_date TEXT
                )
            """)
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(applications)")
            }
            if "follow_up_date" not in columns:
                connection.execute(
                    "ALTER TABLE applications ADD COLUMN follow_up_date TEXT"
                )


def get_follow_up_reminders(today=None, database_path=DATABASE_PATH):
    """Return overdue and next-seven-day follow-ups without changing stored rows."""
    today = today or date.today()
    today_text = today.isoformat()
    horizon_text = (today + timedelta(days=7)).isoformat()

    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("""
            SELECT application_id, company_name, job_role, follow_up_date, status
            FROM applications
            WHERE follow_up_date IS NOT NULL
                AND follow_up_date <= ?
            ORDER BY follow_up_date, company_name COLLATE NOCASE
        """, (horizon_text,)).fetchall()

    reminders = {"overdue": [], "upcoming": []}
    for row in rows:
        reminder = dict(row)
        category = "overdue" if reminder["follow_up_date"] < today_text else "upcoming"
        reminders[category].append(reminder)

    return reminders

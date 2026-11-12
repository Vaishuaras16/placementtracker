import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import date
from pathlib import Path

from database import get_follow_up_reminders, initialize_database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "placements.db"

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_migration_preserves_existing_applications(self):
        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                connection.execute("""
                    CREATE TABLE applications (
                        application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_name TEXT NOT NULL,
                        job_role TEXT NOT NULL,
                        application_date TEXT,
                        status TEXT
                    )
                """)
                connection.execute("""
                    INSERT INTO applications
                        (company_name, job_role, application_date, status)
                    VALUES ('Example Co', 'Engineer', '2026-11-01', 'Applied')
                """)

        initialize_database(self.database_path)

        with closing(sqlite3.connect(self.database_path)) as connection:
            application = connection.execute("""
                SELECT company_name, job_role, application_date, status, follow_up_date
                FROM applications
            """).fetchone()

        self.assertEqual(
            application,
            ("Example Co", "Engineer", "2026-11-01", "Applied", None),
        )

    def test_reminders_separate_overdue_and_next_seven_days(self):
        initialize_database(self.database_path)
        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                connection.executemany("""
                    INSERT INTO applications
                        (company_name, job_role, follow_up_date)
                    VALUES (?, ?, ?)
                """, [
                    ("Overdue Co", "Engineer", "2026-11-11"),
                    ("Today Co", "Engineer", "2026-11-12"),
                    ("In Seven Days Co", "Engineer", "2026-11-19"),
                    ("Later Co", "Engineer", "2026-11-20"),
                    ("No Date Co", "Engineer", None),
                ])

        reminders = get_follow_up_reminders(
            today=date(2026, 11, 12),
            database_path=self.database_path,
        )

        self.assertEqual(
            [item["company_name"] for item in reminders["overdue"]],
            ["Overdue Co"],
        )
        self.assertEqual(
            [item["company_name"] for item in reminders["upcoming"]],
            ["Today Co", "In Seven Days Co"],
        )

    def test_initialize_database_is_safe_to_run_repeatedly(self):
        initialize_database(self.database_path)
        initialize_database(self.database_path)

        with closing(sqlite3.connect(self.database_path)) as connection:
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(applications)")
            }

        self.assertIn("follow_up_date", columns)


if __name__ == "__main__":
    unittest.main()

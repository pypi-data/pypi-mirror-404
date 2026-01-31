"""Tests for database migration."""

import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from folderbot.migration import migrate_database


@pytest.fixture
def old_db_path(tmp_path: Path) -> Path:
    """Create a temporary old database path."""
    return tmp_path / "old" / "sessions.db"


@pytest.fixture
def new_db_path(tmp_path: Path) -> Path:
    """Create a temporary new database path."""
    return tmp_path / "new" / ".folderbot" / "sessions.db"


def create_old_db(old_db_path: Path) -> None:
    """Create an old database with test data."""
    old_db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(old_db_path) as conn:
        conn.execute("""
            CREATE TABLE sessions (
                user_id INTEGER PRIMARY KEY,
                messages TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE user_settings (
                user_id INTEGER PRIMARY KEY,
                last_notified_version TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE scheduled_tasks (
                task_id TEXT PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                steps_json TEXT NOT NULL,
                schedule_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT '',
                started_at TEXT NOT NULL DEFAULT '',
                completed_at TEXT NOT NULL DEFAULT '',
                results_json TEXT NOT NULL DEFAULT '[]',
                current_iteration INTEGER NOT NULL DEFAULT 0,
                max_results_kept INTEGER NOT NULL DEFAULT 100,
                summarize_on_complete INTEGER NOT NULL DEFAULT 1,
                progress_interval INTEGER NOT NULL DEFAULT 1,
                last_error TEXT NOT NULL DEFAULT '',
                consecutive_errors INTEGER NOT NULL DEFAULT 0,
                max_consecutive_errors INTEGER NOT NULL DEFAULT 5,
                next_run_at TEXT NOT NULL DEFAULT '',
                deadline_at TEXT NOT NULL DEFAULT ''
            )
        """)

        # Add test data for user 123
        conn.execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?)",
            (
                123,
                json.dumps([{"role": "user", "content": "hello"}]),
                "2024-01-01",
                "2024-01-01",
            ),
        )
        conn.execute(
            "INSERT INTO user_settings VALUES (?, ?)",
            (123, "0.1.25"),
        )
        conn.execute(
            """INSERT INTO scheduled_tasks
            (task_id, chat_id, user_id, description, steps_json, schedule_json, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("task-1", 123, 123, "test task", "[]", "{}", "pending"),
        )

        # Add test data for user 456 (should not be migrated)
        conn.execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?)",
            (
                456,
                json.dumps([{"role": "user", "content": "other user"}]),
                "2024-01-01",
                "2024-01-01",
            ),
        )

        conn.commit()


def test_migrate_database_copies_user_data(
    old_db_path: Path, new_db_path: Path
) -> None:
    """Test that migration copies data for allowed users."""
    create_old_db(old_db_path)

    with patch("folderbot.migration.OLD_DB_PATH", old_db_path):
        migrate_database(new_db_path, [123])

    # Verify new database has the data
    assert new_db_path.exists()

    with sqlite3.connect(new_db_path) as conn:
        cursor = conn.execute("SELECT * FROM sessions WHERE user_id = 123")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == 123

        cursor = conn.execute("SELECT * FROM user_settings WHERE user_id = 123")
        row = cursor.fetchone()
        assert row is not None
        assert row[1] == "0.1.25"

        cursor = conn.execute("SELECT * FROM scheduled_tasks WHERE user_id = 123")
        row = cursor.fetchone()
        assert row is not None


def test_migrate_database_removes_from_old(
    old_db_path: Path, new_db_path: Path
) -> None:
    """Test that migration removes migrated data from old database."""
    create_old_db(old_db_path)

    with patch("folderbot.migration.OLD_DB_PATH", old_db_path):
        migrate_database(new_db_path, [123])

    # Verify old database no longer has user 123's data
    with sqlite3.connect(old_db_path) as conn:
        cursor = conn.execute("SELECT * FROM sessions WHERE user_id = 123")
        assert cursor.fetchone() is None

        # But user 456's data should still be there
        cursor = conn.execute("SELECT * FROM sessions WHERE user_id = 456")
        assert cursor.fetchone() is not None


def test_migrate_database_deletes_empty_old_db(
    old_db_path: Path, new_db_path: Path
) -> None:
    """Test that empty old database is deleted after migration."""
    # Create old db with only user 123
    old_db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(old_db_path) as conn:
        conn.execute("""
            CREATE TABLE sessions (
                user_id INTEGER PRIMARY KEY,
                messages TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?)",
            (123, "[]", "2024-01-01", "2024-01-01"),
        )
        conn.commit()

    with patch("folderbot.migration.OLD_DB_PATH", old_db_path):
        migrate_database(new_db_path, [123])

    # Old database should be deleted since it's now empty
    assert not old_db_path.exists()


def test_migrate_database_skips_if_new_exists(
    old_db_path: Path, new_db_path: Path
) -> None:
    """Test that migration is skipped if new database already exists."""
    create_old_db(old_db_path)

    # Create empty new database
    new_db_path.parent.mkdir(parents=True, exist_ok=True)
    new_db_path.touch()

    with patch("folderbot.migration.OLD_DB_PATH", old_db_path):
        migrate_database(new_db_path, [123])

    # Old database should still have the data (not migrated)
    with sqlite3.connect(old_db_path) as conn:
        cursor = conn.execute("SELECT * FROM sessions WHERE user_id = 123")
        assert cursor.fetchone() is not None


def test_migrate_database_skips_if_old_missing(new_db_path: Path) -> None:
    """Test that migration handles missing old database gracefully."""
    nonexistent = Path("/nonexistent/path/sessions.db")

    with patch("folderbot.migration.OLD_DB_PATH", nonexistent):
        # Should not raise
        migrate_database(new_db_path, [123])

    assert not new_db_path.exists()


def test_migrate_database_no_data_for_users(
    old_db_path: Path, new_db_path: Path
) -> None:
    """Test migration when old db has no data for the allowed users."""
    create_old_db(old_db_path)

    with patch("folderbot.migration.OLD_DB_PATH", old_db_path):
        migrate_database(new_db_path, [999])  # User not in old db

    # New database should not be created
    assert not new_db_path.exists()

    # Old database should be unchanged
    with sqlite3.connect(old_db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM sessions")
        assert cursor.fetchone()[0] == 2  # Both users still there

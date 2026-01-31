"""Database migration utilities."""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

OLD_DB_PATH = Path.home() / ".local/share/self-bot/sessions.db"


def migrate_database(new_db_path: Path, allowed_user_ids: list[int]) -> None:
    """Migrate user data from old global database to new folder-local database.

    - Checks if old database exists and has data for the allowed users
    - Copies that data to the new database location
    - Removes migrated data from old database
    - Deletes old database if it's empty afterward
    """
    if not OLD_DB_PATH.exists():
        return

    if new_db_path.exists():
        # New database already exists, skip migration
        return

    if not allowed_user_ids:
        return

    logger.info(f"Checking for data to migrate from {OLD_DB_PATH}")

    try:
        _perform_migration(new_db_path, allowed_user_ids)
    except Exception as e:
        logger.warning(f"Migration failed (non-fatal): {e}")


def _perform_migration(new_db_path: Path, allowed_user_ids: list[int]) -> None:
    """Perform the actual migration."""
    # Ensure new db directory exists
    new_db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(OLD_DB_PATH) as old_conn:
        # Check what tables exist in old db
        cursor = old_conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        old_tables = {row[0] for row in cursor.fetchall()}

        if not old_tables:
            return

        placeholders = ",".join("?" for _ in allowed_user_ids)
        migrated_any = False

        with sqlite3.connect(new_db_path) as new_conn:
            # Migrate sessions table
            if "sessions" in old_tables:
                cursor = old_conn.execute(
                    f"SELECT * FROM sessions WHERE user_id IN ({placeholders})",
                    allowed_user_ids,
                )
                rows = cursor.fetchall()

                if rows:
                    # Create table in new db
                    new_conn.execute("""
                        CREATE TABLE IF NOT EXISTS sessions (
                            user_id INTEGER PRIMARY KEY,
                            messages TEXT NOT NULL DEFAULT '[]',
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL
                        )
                    """)

                    new_conn.executemany(
                        "INSERT OR REPLACE INTO sessions VALUES (?, ?, ?, ?)",
                        rows,
                    )
                    logger.info(f"Migrated {len(rows)} session(s)")
                    migrated_any = True

            # Migrate user_settings table
            if "user_settings" in old_tables:
                cursor = old_conn.execute(
                    f"SELECT * FROM user_settings WHERE user_id IN ({placeholders})",
                    allowed_user_ids,
                )
                rows = cursor.fetchall()

                if rows:
                    new_conn.execute("""
                        CREATE TABLE IF NOT EXISTS user_settings (
                            user_id INTEGER PRIMARY KEY,
                            last_notified_version TEXT
                        )
                    """)

                    new_conn.executemany(
                        "INSERT OR REPLACE INTO user_settings VALUES (?, ?)",
                        rows,
                    )
                    logger.info(f"Migrated {len(rows)} user setting(s)")
                    migrated_any = True

            # Migrate scheduled_tasks table
            if "scheduled_tasks" in old_tables:
                cursor = old_conn.execute(
                    f"SELECT * FROM scheduled_tasks WHERE user_id IN ({placeholders})",
                    allowed_user_ids,
                )
                rows = cursor.fetchall()

                if rows:
                    # Get column info from old db
                    cursor = old_conn.execute("PRAGMA table_info(scheduled_tasks)")
                    columns = [row[1] for row in cursor.fetchall()]

                    # Create table with same schema
                    new_conn.execute("""
                        CREATE TABLE IF NOT EXISTS scheduled_tasks (
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

                    placeholders_row = ",".join("?" for _ in columns)
                    new_conn.executemany(
                        f"INSERT OR REPLACE INTO scheduled_tasks ({','.join(columns)}) "
                        f"VALUES ({placeholders_row})",
                        rows,
                    )
                    logger.info(f"Migrated {len(rows)} scheduled task(s)")
                    migrated_any = True

            new_conn.commit()

        if not migrated_any:
            # Nothing to migrate, clean up empty new db if we created it
            if new_db_path.exists():
                new_db_path.unlink()
            return

        # Remove migrated data from old database
        if "sessions" in old_tables:
            old_conn.execute(
                f"DELETE FROM sessions WHERE user_id IN ({placeholders})",
                allowed_user_ids,
            )

        if "user_settings" in old_tables:
            old_conn.execute(
                f"DELETE FROM user_settings WHERE user_id IN ({placeholders})",
                allowed_user_ids,
            )

        if "scheduled_tasks" in old_tables:
            old_conn.execute(
                f"DELETE FROM scheduled_tasks WHERE user_id IN ({placeholders})",
                allowed_user_ids,
            )

        old_conn.commit()
        logger.info("Removed migrated data from old database")

    # Check if old database is now empty and delete if so
    _cleanup_old_database()


def _cleanup_old_database() -> None:
    """Delete old database if it has no remaining user data."""
    if not OLD_DB_PATH.exists():
        return

    with sqlite3.connect(OLD_DB_PATH) as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        total_rows = 0
        for table in tables:
            if table.startswith("sqlite_"):
                continue
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            total_rows += cursor.fetchone()[0]

        if total_rows == 0:
            logger.info(f"Old database is empty, removing {OLD_DB_PATH}")
            OLD_DB_PATH.unlink()

            # Also remove parent directories if empty
            parent = OLD_DB_PATH.parent
            try:
                parent.rmdir()  # Only works if empty
                parent.parent.rmdir()  # ~/.local/share/self-bot -> ~/.local/share
            except OSError:
                pass  # Directory not empty, that's fine

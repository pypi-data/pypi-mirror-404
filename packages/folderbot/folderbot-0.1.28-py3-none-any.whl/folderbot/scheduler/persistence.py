"""SQLite persistence for scheduled tasks."""

import json
import sqlite3
from pathlib import Path

from .models import (
    Schedule,
    ScheduleType,
    TaskPlan,
    TaskResult,
    TaskStatus,
    TaskStep,
)


class TaskStore:
    """Persists task plans to SQLite."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Create tables if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
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
            conn.commit()

            # Migration: add new columns if they don't exist (for existing DBs)
            for column in ["next_run_at", "deadline_at"]:
                try:
                    conn.execute(
                        f"ALTER TABLE scheduled_tasks ADD COLUMN {column} "
                        "TEXT NOT NULL DEFAULT ''"
                    )
                    conn.commit()
                except sqlite3.OperationalError:
                    # Column already exists
                    pass

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def save_task(self, plan: TaskPlan) -> None:
        """Save or update a task plan."""
        steps_json = json.dumps(
            [{"tool_name": s.tool_name, "tool_input": s.tool_input} for s in plan.steps]
        )
        schedule_json = json.dumps(
            {
                "schedule_type": plan.schedule.schedule_type.value,
                "delay_seconds": plan.schedule.delay_seconds,
                "interval_seconds": plan.schedule.interval_seconds,
                "cron_expression": plan.schedule.cron_expression,
                "duration_seconds": plan.schedule.duration_seconds,
                "max_iterations": plan.schedule.max_iterations,
            }
        )
        results_json = json.dumps(
            [
                {
                    "iteration": r.iteration,
                    "timestamp": r.timestamp,
                    "tool_name": r.tool_name,
                    "tool_input": r.tool_input,
                    "content": r.content,
                    "is_error": r.is_error,
                }
                for r in plan.results
            ]
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO scheduled_tasks (
                    task_id, chat_id, user_id, description,
                    steps_json, schedule_json, status,
                    created_at, started_at, completed_at,
                    results_json, current_iteration,
                    max_results_kept, summarize_on_complete, progress_interval,
                    last_error, consecutive_errors, max_consecutive_errors,
                    next_run_at, deadline_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan.task_id,
                    plan.chat_id,
                    plan.user_id,
                    plan.description,
                    steps_json,
                    schedule_json,
                    plan.status.value,
                    plan.created_at,
                    plan.started_at,
                    plan.completed_at,
                    results_json,
                    plan.current_iteration,
                    plan.max_results_kept,
                    int(plan.summarize_on_complete),
                    plan.progress_interval,
                    plan.last_error,
                    plan.consecutive_errors,
                    plan.max_consecutive_errors,
                    plan.next_run_at,
                    plan.deadline_at,
                ),
            )
            conn.commit()

    def load_active_tasks(self) -> list[TaskPlan]:
        """Load all tasks that were pending or running (for restart recovery)."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM scheduled_tasks WHERE status IN (?, ?)",
                (TaskStatus.pending.value, TaskStatus.running.value),
            )
            return [self._row_to_plan(row) for row in cursor.fetchall()]

    def load_user_tasks(self, user_id: int) -> list[TaskPlan]:
        """Load all tasks for a user."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM scheduled_tasks WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            )
            return [self._row_to_plan(row) for row in cursor.fetchall()]

    def _row_to_plan(self, row: tuple) -> TaskPlan:  # type: ignore[type-arg]
        """Convert a database row to a TaskPlan."""
        steps_data = json.loads(row[4])
        schedule_data = json.loads(row[5])
        results_data = json.loads(row[10])

        steps = tuple(
            TaskStep(tool_name=s["tool_name"], tool_input=s["tool_input"])
            for s in steps_data
        )
        schedule = Schedule(
            schedule_type=ScheduleType(schedule_data["schedule_type"]),
            delay_seconds=schedule_data["delay_seconds"],
            interval_seconds=schedule_data["interval_seconds"],
            cron_expression=schedule_data["cron_expression"],
            duration_seconds=schedule_data["duration_seconds"],
            max_iterations=schedule_data["max_iterations"],
        )
        results = tuple(
            TaskResult(
                iteration=r["iteration"],
                timestamp=r["timestamp"],
                tool_name=r["tool_name"],
                tool_input=r["tool_input"],
                content=r["content"],
                is_error=r["is_error"],
            )
            for r in results_data
        )

        # Handle both old (18 columns) and new (20 columns) schema
        next_run_at = row[18] if len(row) > 18 else ""
        deadline_at = row[19] if len(row) > 19 else ""

        return TaskPlan(
            task_id=row[0],
            chat_id=row[1],
            user_id=row[2],
            description=row[3],
            steps=steps,
            schedule=schedule,
            status=TaskStatus(row[6]),
            created_at=row[7] or "",
            started_at=row[8] or "",
            completed_at=row[9] or "",
            next_run_at=next_run_at or "",
            deadline_at=deadline_at or "",
            results=results,
            current_iteration=row[11],
            max_results_kept=row[12],
            summarize_on_complete=bool(row[13]),
            progress_interval=row[14],
            last_error=row[15] or "",
            consecutive_errors=row[16],
            max_consecutive_errors=row[17],
        )

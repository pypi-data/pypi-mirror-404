"""Tests for scheduler persistence."""

from pathlib import Path

import pytest

from folderbot.scheduler.models import (
    Schedule,
    ScheduleType,
    TaskPlan,
    TaskResult,
    TaskStatus,
    TaskStep,
)
from folderbot.scheduler.persistence import TaskStore


@pytest.fixture
def task_store(tmp_path: Path) -> TaskStore:
    """Create a task store with a temporary database."""
    db_path = tmp_path / "test_tasks.db"
    return TaskStore(db_path)


def _make_plan(
    task_id: str = "task001",
    chat_id: int = 100,
    user_id: int = 200,
    status: TaskStatus = TaskStatus.pending,
    results: tuple[TaskResult, ...] = (),
) -> TaskPlan:
    """Helper to create a TaskPlan for testing."""
    return TaskPlan(
        task_id=task_id,
        chat_id=chat_id,
        user_id=user_id,
        description="Test task",
        steps=(TaskStep(tool_name="read_file", tool_input={"path": "a.md"}),),
        schedule=Schedule(
            schedule_type=ScheduleType.repeating,
            interval_seconds=60,
            max_iterations=5,
        ),
        status=status,
        created_at="2025-01-01T00:00:00+00:00",
        results=results,
    )


class TestTaskStore:
    def test_creates_database(self, tmp_path: Path):
        db_path = tmp_path / "subdir" / "tasks.db"
        TaskStore(db_path)

        assert db_path.exists()
        assert db_path.parent.exists()

    def test_save_and_load_active(self, task_store: TaskStore):
        plan = _make_plan(status=TaskStatus.pending)
        task_store.save_task(plan)

        active = task_store.load_active_tasks()

        assert len(active) == 1
        assert active[0].task_id == "task001"
        assert active[0].status == TaskStatus.pending

    def test_load_active_includes_running(self, task_store: TaskStore):
        task_store.save_task(_make_plan(task_id="t1", status=TaskStatus.pending))
        task_store.save_task(_make_plan(task_id="t2", status=TaskStatus.running))
        task_store.save_task(_make_plan(task_id="t3", status=TaskStatus.completed))

        active = task_store.load_active_tasks()

        active_ids = {t.task_id for t in active}
        assert active_ids == {"t1", "t2"}

    def test_load_user_tasks(self, task_store: TaskStore):
        task_store.save_task(_make_plan(task_id="t1", user_id=100))
        task_store.save_task(_make_plan(task_id="t2", user_id=200))
        task_store.save_task(_make_plan(task_id="t3", user_id=100))

        tasks = task_store.load_user_tasks(user_id=100)

        task_ids = {t.task_id for t in tasks}
        assert task_ids == {"t1", "t3"}

    def test_save_preserves_schedule(self, task_store: TaskStore):
        plan = _make_plan()
        task_store.save_task(plan)

        loaded = task_store.load_active_tasks()[0]

        assert loaded.schedule.schedule_type == ScheduleType.repeating
        assert loaded.schedule.interval_seconds == 60
        assert loaded.schedule.max_iterations == 5

    def test_save_preserves_steps(self, task_store: TaskStore):
        plan = TaskPlan(
            task_id="multi",
            chat_id=100,
            user_id=200,
            description="Multi-step task",
            steps=(
                TaskStep(tool_name="read_file", tool_input={"path": "a.md"}),
                TaskStep(tool_name="search_files", tool_input={"query": "test"}),
            ),
            schedule=Schedule(schedule_type=ScheduleType.once),
            status=TaskStatus.pending,
            created_at="2025-01-01T00:00:00+00:00",
        )
        task_store.save_task(plan)

        loaded = task_store.load_active_tasks()[0]

        assert len(loaded.steps) == 2
        assert loaded.steps[0].tool_name == "read_file"
        assert loaded.steps[1].tool_name == "search_files"

    def test_save_preserves_results(self, task_store: TaskStore):
        result = TaskResult(
            iteration=1,
            timestamp="2025-01-01T00:00:00+00:00",
            tool_name="read_file",
            tool_input={"path": "a.md"},
            content="file contents",
            is_error=False,
        )
        plan = _make_plan(results=(result,))
        task_store.save_task(plan)

        loaded = task_store.load_active_tasks()[0]

        assert len(loaded.results) == 1
        assert loaded.results[0].content == "file contents"
        assert loaded.results[0].iteration == 1

    def test_upsert_updates_existing(self, task_store: TaskStore):
        plan = _make_plan(status=TaskStatus.pending)
        task_store.save_task(plan)

        from dataclasses import replace

        updated = replace(plan, status=TaskStatus.running)
        task_store.save_task(updated)

        active = task_store.load_active_tasks()

        assert len(active) == 1
        assert active[0].status == TaskStatus.running

    def test_empty_results(self, task_store: TaskStore):
        active = task_store.load_active_tasks()

        assert active == []

    def test_preserves_all_fields(self, task_store: TaskStore):
        plan = TaskPlan(
            task_id="full",
            chat_id=100,
            user_id=200,
            description="Full task",
            steps=(TaskStep(tool_name="read_file", tool_input={"path": "a.md"}),),
            schedule=Schedule(
                schedule_type=ScheduleType.cron,
                cron_expression="0 9 * * *",
                max_iterations=10,
            ),
            status=TaskStatus.running,
            created_at="2025-01-01T00:00:00+00:00",
            started_at="2025-01-01T00:01:00+00:00",
            max_results_kept=50,
            summarize_on_complete=False,
            progress_interval=5,
            last_error="some error",
            consecutive_errors=2,
            max_consecutive_errors=3,
        )
        task_store.save_task(plan)

        loaded = task_store.load_active_tasks()[0]

        assert loaded.task_id == "full"
        assert loaded.max_results_kept == 50
        assert loaded.summarize_on_complete is False
        assert loaded.progress_interval == 5
        assert loaded.last_error == "some error"
        assert loaded.consecutive_errors == 2
        assert loaded.max_consecutive_errors == 3
        assert loaded.schedule.cron_expression == "0 9 * * *"

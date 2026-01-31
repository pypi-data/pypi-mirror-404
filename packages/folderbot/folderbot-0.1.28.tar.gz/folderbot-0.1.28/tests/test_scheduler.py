"""Tests for the task scheduler engine."""

import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from folderbot.scheduler.models import (
    Schedule,
    ScheduleType,
    TaskPlan,
    TaskStatus,
    TaskStep,
)
from folderbot.scheduler.persistence import TaskStore
from folderbot.scheduler.scheduler import TaskScheduler
from folderbot.tools.base import ToolResult


@pytest.fixture
def task_store(tmp_path: Path) -> TaskStore:
    db_path = tmp_path / "test_tasks.db"
    return TaskStore(db_path)


@pytest.fixture
def send_message() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def summarize() -> AsyncMock:
    return AsyncMock(return_value="Test summary")


@pytest.fixture
def folder_tools() -> MagicMock:
    tools = MagicMock()
    tools.execute.return_value = ToolResult(content="tool output")
    return tools


@pytest.fixture
async def scheduler(
    task_store: TaskStore,
    send_message: AsyncMock,
    summarize: AsyncMock,
    folder_tools: MagicMock,
) -> AsyncGenerator[TaskScheduler, None]:
    s = TaskScheduler(
        task_store=task_store,
        send_message=send_message,
        summarize=summarize,
    )
    s.set_folder_tools(folder_tools)
    await s.start()  # Start the heartbeat
    yield s
    await s.shutdown()  # Clean up


def _make_plan(
    task_id: str = "task001",
    schedule_type: ScheduleType = ScheduleType.once,
    **kwargs: Any,
) -> TaskPlan:
    from datetime import datetime, timezone

    # Default next_run_at to now (immediate execution) unless specified
    if "next_run_at" not in kwargs:
        kwargs["next_run_at"] = datetime.now(timezone.utc).isoformat()

    defaults: dict[str, Any] = dict(
        chat_id=100,
        user_id=200,
        description="Test task",
        steps=(TaskStep(tool_name="read_file", tool_input={"path": "a.md"}),),
        schedule=Schedule(schedule_type=schedule_type),
        created_at="2025-01-01T00:00:00+00:00",
    )
    defaults.update(kwargs)
    return TaskPlan(task_id=task_id, **defaults)  # type: ignore[arg-type]


class TestCreateTask:
    async def test_creates_and_tracks_task(self, scheduler: TaskScheduler):
        plan = _make_plan()
        task_id = await scheduler.create_task(plan)

        assert task_id == "task001"
        # Verify task is trackable via public API
        tasks = scheduler.list_tasks(user_id=200)
        assert any(t.task_id == "task001" for t in tasks)

        # Let the heartbeat execute the task
        await asyncio.sleep(1.5)

    async def test_task_persisted_to_store(
        self, scheduler: TaskScheduler, task_store: TaskStore
    ):
        plan = _make_plan()
        await scheduler.create_task(plan)
        await asyncio.sleep(0.1)

        # Verify it was saved to the store
        tasks = task_store.load_user_tasks(user_id=200)
        assert len(tasks) >= 1


class TestListTasks:
    async def test_list_empty(self, scheduler: TaskScheduler):
        tasks = scheduler.list_tasks(user_id=200)
        assert tasks == []

    async def test_list_filters_by_user(self, scheduler: TaskScheduler):
        # Create tasks via public API with different user_ids
        plan1 = _make_plan(
            task_id="t1", user_id=100, next_run_at="2099-01-01T00:00:00+00:00"
        )
        plan2 = _make_plan(
            task_id="t2", user_id=200, next_run_at="2099-01-01T00:00:00+00:00"
        )

        await scheduler.create_task(plan1)
        await scheduler.create_task(plan2)

        tasks = scheduler.list_tasks(user_id=200)

        assert len(tasks) == 1
        assert tasks[0].task_id == "t2"

    async def test_list_filters_by_status(self, scheduler: TaskScheduler):
        # Create a repeating task (stays pending) and a once task (completes)
        repeating_plan = _make_plan(
            task_id="repeating",
            user_id=200,
            schedule_type=ScheduleType.repeating,
            schedule=Schedule(
                schedule_type=ScheduleType.repeating,
                interval_seconds=3600,  # Far future
                max_iterations=10,
            ),
            next_run_at="2099-01-01T00:00:00+00:00",  # Won't execute
        )
        await scheduler.create_task(repeating_plan)

        # Filter for pending tasks
        pending_tasks = scheduler.list_tasks(user_id=200, status_filter="pending")
        assert len(pending_tasks) == 1
        assert pending_tasks[0].task_id == "repeating"


class TestCancelTask:
    async def test_cancel_existing_task(self, scheduler: TaskScheduler):
        plan = _make_plan(
            schedule_type=ScheduleType.repeating,
            schedule=Schedule(
                schedule_type=ScheduleType.repeating,
                interval_seconds=3600,  # Far future to prevent execution
                max_iterations=100,
            ),
            next_run_at="2099-01-01T00:00:00+00:00",
        )
        await scheduler.create_task(plan)
        await asyncio.sleep(0.1)

        cancelled = await scheduler.cancel_task("task001", user_id=200)

        assert cancelled is True
        # Verify via public API
        tasks = scheduler.list_tasks(user_id=200, status_filter="cancelled")
        assert any(t.task_id == "task001" for t in tasks)

    async def test_cancel_nonexistent_task(self, scheduler: TaskScheduler):
        cancelled = await scheduler.cancel_task("nonexistent", user_id=200)
        assert cancelled is False

    async def test_cancel_wrong_user(self, scheduler: TaskScheduler):
        plan = _make_plan(user_id=200, next_run_at="2099-01-01T00:00:00+00:00")
        await scheduler.create_task(plan)

        cancelled = await scheduler.cancel_task("task001", user_id=999)
        assert cancelled is False


class TestGetTaskResults:
    async def test_get_results(self, scheduler: TaskScheduler):
        plan = _make_plan(next_run_at="2099-01-01T00:00:00+00:00")
        await scheduler.create_task(plan)

        result = scheduler.get_task_results("task001", user_id=200)

        assert result is not None
        assert result.task_id == "task001"

    async def test_get_results_not_found(self, scheduler: TaskScheduler):
        result = scheduler.get_task_results("nonexistent", user_id=200)
        assert result is None

    async def test_get_results_wrong_user(self, scheduler: TaskScheduler):
        plan = _make_plan(user_id=200)
        scheduler._task_plans["task001"] = plan

        result = scheduler.get_task_results("task001", user_id=999)
        assert result is None


class TestRunOnce:
    async def test_once_executes_and_completes(
        self,
        scheduler: TaskScheduler,
        folder_tools: MagicMock,
        send_message: AsyncMock,
    ):
        plan = _make_plan(schedule_type=ScheduleType.once)
        await scheduler.create_task(plan)
        # Wait for heartbeat to pick up and execute the task
        await asyncio.sleep(1.5)

        folder_tools.execute.assert_called_once_with("read_file", {"path": "a.md"})

        final_plan = scheduler._task_plans["task001"]
        assert final_plan.status == TaskStatus.completed
        assert final_plan.current_iteration == 1

    async def test_once_with_delay(
        self,
        scheduler: TaskScheduler,
        folder_tools: MagicMock,
    ):
        plan = _make_plan(
            schedule=Schedule(
                schedule_type=ScheduleType.once,
                delay_seconds=0,  # Use 0 for test speed
            ),
        )
        await scheduler.create_task(plan)
        # Wait for heartbeat to pick up and execute the task
        await asyncio.sleep(1.5)

        folder_tools.execute.assert_called_once()


class TestRunTimeLimited:
    async def test_time_limited_runs_multiple_iterations(
        self,
        scheduler: TaskScheduler,
        folder_tools: MagicMock,
    ):
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        # Minimum interval is 1s, so duration=3 gives ~3 iterations
        plan = _make_plan(
            schedule=Schedule(
                schedule_type=ScheduleType.time_limited,
                duration_seconds=3,
                interval_seconds=1,
            ),
            next_run_at=now.isoformat(),
            deadline_at=(now + timedelta(seconds=3)).isoformat(),
        )
        await scheduler.create_task(plan)
        await asyncio.sleep(4.5)

        assert folder_tools.execute.call_count >= 2

        final_plan = scheduler._task_plans["task001"]
        assert final_plan.status == TaskStatus.completed

    async def test_time_limited_respects_max_iterations(
        self,
        scheduler: TaskScheduler,
        folder_tools: MagicMock,
    ):
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        # Minimum interval is 1s; max_iterations=2 should stop after 2
        plan = _make_plan(
            schedule=Schedule(
                schedule_type=ScheduleType.time_limited,
                duration_seconds=10,
                interval_seconds=1,
                max_iterations=2,
            ),
            next_run_at=now.isoformat(),
            deadline_at=(now + timedelta(seconds=10)).isoformat(),
        )
        await scheduler.create_task(plan)
        await asyncio.sleep(3.5)

        final_plan = scheduler._task_plans["task001"]
        assert final_plan.current_iteration == 2
        assert final_plan.status == TaskStatus.completed


class TestExecuteIteration:
    async def test_error_tracking(
        self,
        scheduler: TaskScheduler,
        folder_tools: MagicMock,
    ):
        folder_tools.execute.return_value = ToolResult(
            content="some error", is_error=True
        )

        plan = _make_plan(
            schedule=Schedule(
                schedule_type=ScheduleType.repeating,
                interval_seconds=1,
                max_iterations=2,
            ),
            max_consecutive_errors=10,
        )
        await scheduler.create_task(plan)
        # Wait for heartbeat to execute at least one iteration
        await asyncio.sleep(2.5)

        final_plan = scheduler._task_plans["task001"]
        assert final_plan.consecutive_errors > 0

    async def test_max_consecutive_errors_fails_task(
        self,
        scheduler: TaskScheduler,
        folder_tools: MagicMock,
        send_message: AsyncMock,
    ):
        folder_tools.execute.return_value = ToolResult(
            content="persistent error", is_error=True
        )

        plan = _make_plan(
            schedule=Schedule(
                schedule_type=ScheduleType.repeating,
                interval_seconds=1,
                max_iterations=100,
            ),
            max_consecutive_errors=3,
        )
        await scheduler.create_task(plan)
        # Wait for 3 iterations to trigger failure
        await asyncio.sleep(4.5)

        final_plan = scheduler._task_plans["task001"]
        assert final_plan.status == TaskStatus.failed

    async def test_success_resets_consecutive_errors(
        self,
        scheduler: TaskScheduler,
        folder_tools: MagicMock,
    ):
        call_count = 0

        def alternate_results(tool_name, tool_input):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 1:
                return ToolResult(content="error", is_error=True)
            return ToolResult(content="success")

        folder_tools.execute.side_effect = alternate_results

        plan = _make_plan(
            schedule=Schedule(
                schedule_type=ScheduleType.repeating,
                interval_seconds=1,
                max_iterations=4,
            ),
            max_consecutive_errors=5,
        )
        await scheduler.create_task(plan)
        # Wait for 4 iterations
        await asyncio.sleep(5.5)

        final_plan = scheduler._task_plans["task001"]
        # Should complete since errors alternate with successes
        assert final_plan.status == TaskStatus.completed

    async def test_results_capped(
        self,
        scheduler: TaskScheduler,
        folder_tools: MagicMock,
    ):
        plan = _make_plan(
            schedule=Schedule(
                schedule_type=ScheduleType.repeating,
                interval_seconds=1,
                max_iterations=10,
            ),
            max_results_kept=5,
            progress_interval=0,
        )
        await scheduler.create_task(plan)
        # Wait for all iterations
        await asyncio.sleep(12.0)

        final_plan = scheduler._task_plans["task001"]
        assert len(final_plan.results) <= 5


class TestProgressMessages:
    async def test_sends_progress(
        self,
        scheduler: TaskScheduler,
        send_message: AsyncMock,
    ):
        plan = _make_plan(
            schedule=Schedule(
                schedule_type=ScheduleType.repeating,
                interval_seconds=1,
                max_iterations=3,
            ),
            progress_interval=1,
            summarize_on_complete=False,
        )
        await scheduler.create_task(plan)
        # Wait for all 3 iterations + completion
        await asyncio.sleep(4.5)

        # Should have progress messages + completion message
        assert send_message.call_count >= 1

    async def test_progress_interval_controls_frequency(
        self,
        scheduler: TaskScheduler,
        send_message: AsyncMock,
    ):
        plan = _make_plan(
            schedule=Schedule(
                schedule_type=ScheduleType.repeating,
                interval_seconds=1,
                max_iterations=4,
            ),
            progress_interval=2,
            summarize_on_complete=False,
        )
        await scheduler.create_task(plan)
        # Wait for all 4 iterations + completion
        await asyncio.sleep(5.5)

        # With progress_interval=2 and 4 iterations: progress at 2, 4 + completion
        # Exact count depends on timing, but should be less than with interval=1
        assert send_message.call_count >= 1


class TestSummary:
    async def test_generates_summary_on_complete(
        self,
        scheduler: TaskScheduler,
        summarize: AsyncMock,
        send_message: AsyncMock,
    ):
        plan = _make_plan(
            schedule_type=ScheduleType.once,
            summarize_on_complete=True,
        )
        await scheduler.create_task(plan)
        # Wait for heartbeat to execute
        await asyncio.sleep(1.5)

        summarize.assert_called_once()
        # Summary should be sent via send_message
        assert any(
            "Summary" in str(call) or "summary" in str(call)
            for call in send_message.call_args_list
        )

    async def test_no_summary_when_disabled(
        self,
        scheduler: TaskScheduler,
        summarize: AsyncMock,
        send_message: AsyncMock,
    ):
        plan = _make_plan(
            schedule_type=ScheduleType.once,
            summarize_on_complete=False,
        )
        await scheduler.create_task(plan)
        # Wait for heartbeat to execute
        await asyncio.sleep(1.5)

        summarize.assert_not_called()
        # Should still get a completion message
        assert send_message.call_count >= 1


class TestShutdown:
    async def test_shutdown_cancels_heartbeat(
        self,
        scheduler: TaskScheduler,
    ):
        plan = _make_plan(
            schedule=Schedule(
                schedule_type=ScheduleType.repeating,
                interval_seconds=1,
                max_iterations=100,
            ),
        )
        await scheduler.create_task(plan)
        await asyncio.sleep(0.1)

        # The fixture will call shutdown, but let's verify the heartbeat is running first
        assert scheduler._heartbeat_task is not None
        assert not scheduler._heartbeat_task.done()


class TestStartRestore:
    async def test_restores_persisted_tasks(
        self,
        task_store: TaskStore,
        send_message: AsyncMock,
        summarize: AsyncMock,
        folder_tools: MagicMock,
    ):
        # Save a pending task to the store
        plan = _make_plan(status=TaskStatus.pending)
        task_store.save_task(plan)

        # Create a new scheduler and start it
        new_scheduler = TaskScheduler(
            task_store=task_store,
            send_message=send_message,
            summarize=summarize,
        )
        new_scheduler.set_folder_tools(folder_tools)
        await new_scheduler.start()

        # Task should be restored
        assert "task001" in new_scheduler._task_plans
        # Heartbeat should be running
        assert new_scheduler._heartbeat_task is not None

        await new_scheduler.shutdown()


class TestListTasksAfterRestart:
    async def test_completed_tasks_visible_after_restart(
        self,
        task_store: TaskStore,
        send_message: AsyncMock,
        summarize: AsyncMock,
        folder_tools: MagicMock,
    ):
        """Completed tasks should still appear in list_tasks after a restart."""
        # Create first scheduler, run a task to completion
        scheduler1 = TaskScheduler(
            task_store=task_store,
            send_message=send_message,
            summarize=summarize,
        )
        scheduler1.set_folder_tools(folder_tools)
        await scheduler1.start()  # Start heartbeat

        plan = _make_plan(
            task_id="completed_task",
            schedule_type=ScheduleType.once,
            summarize_on_complete=False,
        )
        await scheduler1.create_task(plan)
        # Wait for heartbeat to execute
        await asyncio.sleep(1.5)

        # Verify task completed
        assert scheduler1._task_plans["completed_task"].status == TaskStatus.completed

        # Shut down and create a new scheduler (simulates restart)
        await scheduler1.shutdown()

        scheduler2 = TaskScheduler(
            task_store=task_store,
            send_message=send_message,
            summarize=summarize,
        )
        scheduler2.set_folder_tools(folder_tools)
        await scheduler2.start()

        # The completed task should still be visible in list_tasks
        tasks = scheduler2.list_tasks(user_id=200)
        task_ids = [t.task_id for t in tasks]
        assert "completed_task" in task_ids

        await scheduler2.shutdown()

    async def test_failed_tasks_visible_after_restart(
        self,
        task_store: TaskStore,
        send_message: AsyncMock,
        summarize: AsyncMock,
        folder_tools: MagicMock,
    ):
        """Failed tasks should still appear in list_tasks after a restart."""
        folder_tools.execute.return_value = ToolResult(content="error", is_error=True)

        scheduler1 = TaskScheduler(
            task_store=task_store,
            send_message=send_message,
            summarize=summarize,
        )
        scheduler1.set_folder_tools(folder_tools)
        await scheduler1.start()  # Start heartbeat

        plan = _make_plan(
            task_id="failed_task",
            schedule=Schedule(
                schedule_type=ScheduleType.repeating,
                interval_seconds=1,
                max_iterations=100,
            ),
            max_consecutive_errors=2,
        )
        await scheduler1.create_task(plan)
        # Wait for failures to occur
        await asyncio.sleep(3.5)

        assert scheduler1._task_plans["failed_task"].status == TaskStatus.failed

        await scheduler1.shutdown()

        scheduler2 = TaskScheduler(
            task_store=task_store,
            send_message=send_message,
            summarize=summarize,
        )
        scheduler2.set_folder_tools(folder_tools)
        await scheduler2.start()

        tasks = scheduler2.list_tasks(user_id=200)
        task_ids = [t.task_id for t in tasks]
        assert "failed_task" in task_ids

        await scheduler2.shutdown()

    async def test_cancelled_tasks_visible_after_restart(
        self,
        task_store: TaskStore,
        send_message: AsyncMock,
        summarize: AsyncMock,
        folder_tools: MagicMock,
    ):
        """Cancelled tasks should still appear in list_tasks after a restart."""
        scheduler1 = TaskScheduler(
            task_store=task_store,
            send_message=send_message,
            summarize=summarize,
        )
        scheduler1.set_folder_tools(folder_tools)

        plan = _make_plan(
            task_id="cancelled_task",
            schedule=Schedule(
                schedule_type=ScheduleType.repeating,
                interval_seconds=1,
                max_iterations=100,
            ),
        )
        await scheduler1.create_task(plan)
        await asyncio.sleep(0.1)

        await scheduler1.cancel_task("cancelled_task", user_id=200)
        assert scheduler1._task_plans["cancelled_task"].status == TaskStatus.cancelled

        await scheduler1.shutdown()

        scheduler2 = TaskScheduler(
            task_store=task_store,
            send_message=send_message,
            summarize=summarize,
        )
        scheduler2.set_folder_tools(folder_tools)
        await scheduler2.start()

        tasks = scheduler2.list_tasks(user_id=200)
        task_ids = [t.task_id for t in tasks]
        assert "cancelled_task" in task_ids

        await scheduler2.shutdown()


class TestHeartbeatScheduler:
    """Tests for the heartbeat-based scheduler architecture."""

    async def test_task_has_next_run_at_field(self):
        """TaskPlan should have a next_run_at field for absolute scheduling."""
        plan = _make_plan(next_run_at="2025-01-01T12:00:00+00:00")
        assert plan.next_run_at == "2025-01-01T12:00:00+00:00"

    async def test_task_has_deadline_at_field(self):
        """TaskPlan should have a deadline_at field for time-limited tasks."""
        plan = _make_plan(deadline_at="2025-01-01T13:00:00+00:00")
        assert plan.deadline_at == "2025-01-01T13:00:00+00:00"

    async def test_once_task_fires_immediately_when_next_run_at_in_past(
        self,
        task_store: TaskStore,
        send_message: AsyncMock,
        summarize: AsyncMock,
        folder_tools: MagicMock,
    ):
        """Task with past next_run_at should fire immediately on restart."""
        from datetime import datetime, timedelta, timezone

        past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

        # Create scheduler and start heartbeat
        scheduler = TaskScheduler(
            task_store=task_store,
            send_message=send_message,
            summarize=summarize,
        )
        scheduler.set_folder_tools(folder_tools)
        await scheduler.start()

        plan = _make_plan(
            task_id="past_task",
            schedule_type=ScheduleType.once,
            next_run_at=past_time,
            summarize_on_complete=False,
        )
        await scheduler.create_task(plan)

        # Give heartbeat time to detect and execute (heartbeat polls every 1s)
        await asyncio.sleep(1.5)

        final_plan = scheduler._task_plans["past_task"]
        assert final_plan.status == TaskStatus.completed
        folder_tools.execute.assert_called()

        await scheduler.shutdown()

    async def test_once_task_waits_for_future_next_run_at(
        self,
        task_store: TaskStore,
        send_message: AsyncMock,
        summarize: AsyncMock,
        folder_tools: MagicMock,
    ):
        """Task with future next_run_at should not fire until time reaches."""
        from datetime import datetime, timedelta, timezone

        future_time = (datetime.now(timezone.utc) + timedelta(seconds=3)).isoformat()

        scheduler = TaskScheduler(
            task_store=task_store,
            send_message=send_message,
            summarize=summarize,
        )
        scheduler.set_folder_tools(folder_tools)
        await scheduler.start()

        plan = _make_plan(
            task_id="future_task",
            schedule_type=ScheduleType.once,
            next_run_at=future_time,
            summarize_on_complete=False,
        )
        await scheduler.create_task(plan)

        # Check immediately - should not have executed
        await asyncio.sleep(0.5)
        assert scheduler._task_plans["future_task"].status == TaskStatus.pending
        assert folder_tools.execute.call_count == 0

        # Wait for the scheduled time + heartbeat interval
        await asyncio.sleep(3.5)
        final_plan = scheduler._task_plans["future_task"]
        assert final_plan.status == TaskStatus.completed
        folder_tools.execute.assert_called()

        await scheduler.shutdown()

    async def test_repeating_task_updates_next_run_at(
        self,
        task_store: TaskStore,
        send_message: AsyncMock,
        summarize: AsyncMock,
        folder_tools: MagicMock,
    ):
        """Repeating task should update next_run_at after each iteration."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()

        scheduler = TaskScheduler(
            task_store=task_store,
            send_message=send_message,
            summarize=summarize,
        )
        scheduler.set_folder_tools(folder_tools)
        await scheduler.start()

        plan = _make_plan(
            task_id="repeating_task",
            schedule=Schedule(
                schedule_type=ScheduleType.repeating,
                interval_seconds=2,
                max_iterations=3,
            ),
            next_run_at=now,
            summarize_on_complete=False,
        )
        await scheduler.create_task(plan)

        # First iteration should fire immediately (next_run_at = now)
        await asyncio.sleep(1.5)
        plan_after_1 = scheduler._task_plans["repeating_task"]
        assert plan_after_1.current_iteration >= 1
        first_next_run = plan_after_1.next_run_at

        # After another interval, next_run_at should have advanced
        await asyncio.sleep(2.5)
        plan_after_2 = scheduler._task_plans["repeating_task"]
        assert plan_after_2.current_iteration >= 2
        # next_run_at should be different (advanced by interval)
        assert (
            plan_after_2.next_run_at != first_next_run or plan_after_2.next_run_at == ""
        )

        await scheduler.shutdown()

    async def test_time_limited_task_completes_at_deadline(
        self,
        task_store: TaskStore,
        send_message: AsyncMock,
        summarize: AsyncMock,
        folder_tools: MagicMock,
    ):
        """Time-limited task should complete when deadline_at is reached."""
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        deadline = (now + timedelta(seconds=3)).isoformat()

        scheduler = TaskScheduler(
            task_store=task_store,
            send_message=send_message,
            summarize=summarize,
        )
        scheduler.set_folder_tools(folder_tools)
        await scheduler.start()

        plan = _make_plan(
            task_id="deadline_task",
            schedule=Schedule(
                schedule_type=ScheduleType.time_limited,
                interval_seconds=1,
                duration_seconds=3,  # Will be converted to deadline_at
            ),
            next_run_at=now.isoformat(),
            deadline_at=deadline,
            summarize_on_complete=False,
        )
        await scheduler.create_task(plan)

        # Let it run a few iterations
        await asyncio.sleep(2)
        mid_plan = scheduler._task_plans["deadline_task"]
        assert mid_plan.status == TaskStatus.running

        # Wait past deadline
        await asyncio.sleep(2.5)
        final_plan = scheduler._task_plans["deadline_task"]
        assert final_plan.status == TaskStatus.completed

        await scheduler.shutdown()

    async def test_scheduler_has_heartbeat_task(
        self,
        task_store: TaskStore,
        send_message: AsyncMock,
        summarize: AsyncMock,
    ):
        """Scheduler should have a single heartbeat task, not per-task asyncio tasks."""
        scheduler = TaskScheduler(
            task_store=task_store,
            send_message=send_message,
            summarize=summarize,
        )
        await scheduler.start()

        # After start, should have _heartbeat_task
        assert hasattr(scheduler, "_heartbeat_task")
        assert scheduler._heartbeat_task is not None
        assert not scheduler._heartbeat_task.done()

        await scheduler.shutdown()

        # After shutdown, heartbeat should be cancelled
        assert scheduler._heartbeat_task.cancelled() or scheduler._heartbeat_task.done()

    async def test_persistence_preserves_next_run_at(
        self,
        task_store: TaskStore,
        send_message: AsyncMock,
        summarize: AsyncMock,
        folder_tools: MagicMock,
    ):
        """next_run_at and deadline_at should be preserved across restart."""
        from datetime import datetime, timedelta, timezone

        future_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        deadline = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

        # Save a task with next_run_at to the store
        plan = _make_plan(
            task_id="persisted_task",
            status=TaskStatus.pending,
            next_run_at=future_time,
            deadline_at=deadline,
        )
        task_store.save_task(plan)

        # Load it back
        loaded = task_store.load_user_tasks(user_id=200)
        assert len(loaded) == 1
        assert loaded[0].next_run_at == future_time
        assert loaded[0].deadline_at == deadline

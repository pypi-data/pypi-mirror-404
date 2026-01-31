"""Tests for scheduler data models."""

from dataclasses import replace

from folderbot.scheduler.models import (
    Schedule,
    ScheduleType,
    TaskPlan,
    TaskResult,
    TaskStatus,
    TaskStep,
)


class TestScheduleType:
    def test_values(self):
        assert ScheduleType.once == "once"
        assert ScheduleType.repeating == "repeating"
        assert ScheduleType.cron == "cron"
        assert ScheduleType.time_limited == "time_limited"

    def test_from_string(self):
        assert ScheduleType("once") is ScheduleType.once
        assert ScheduleType("repeating") is ScheduleType.repeating


class TestTaskStatus:
    def test_values(self):
        assert TaskStatus.pending == "pending"
        assert TaskStatus.running == "running"
        assert TaskStatus.completed == "completed"
        assert TaskStatus.cancelled == "cancelled"
        assert TaskStatus.failed == "failed"


class TestTaskStep:
    def test_creation(self):
        step = TaskStep(tool_name="read_file", tool_input={"path": "readme.md"})

        assert step.tool_name == "read_file"
        assert step.tool_input == {"path": "readme.md"}

    def test_frozen(self):
        step = TaskStep(tool_name="read_file", tool_input={"path": "readme.md"})
        try:
            step.tool_name = "write_file"  # type: ignore[misc]
            assert False, "Should raise FrozenInstanceError"
        except AttributeError:
            pass


class TestSchedule:
    def test_defaults(self):
        schedule = Schedule(schedule_type=ScheduleType.once)

        assert schedule.delay_seconds == 0
        assert schedule.interval_seconds == 0
        assert schedule.cron_expression == ""
        assert schedule.duration_seconds == 0
        assert schedule.max_iterations == 0

    def test_repeating_schedule(self):
        schedule = Schedule(
            schedule_type=ScheduleType.repeating,
            interval_seconds=60,
            max_iterations=10,
        )

        assert schedule.schedule_type == ScheduleType.repeating
        assert schedule.interval_seconds == 60
        assert schedule.max_iterations == 10

    def test_time_limited_schedule(self):
        schedule = Schedule(
            schedule_type=ScheduleType.time_limited,
            duration_seconds=300,
            interval_seconds=5,
        )

        assert schedule.duration_seconds == 300
        assert schedule.interval_seconds == 5


class TestTaskResult:
    def test_creation(self):
        result = TaskResult(
            iteration=1,
            timestamp="2025-01-01T00:00:00+00:00",
            tool_name="search_files",
            tool_input={"query": "test"},
            content="found something",
            is_error=False,
        )

        assert result.iteration == 1
        assert result.tool_name == "search_files"
        assert result.content == "found something"
        assert not result.is_error


class TestTaskPlan:
    def test_defaults(self):
        plan = TaskPlan(
            task_id="abc123",
            chat_id=100,
            user_id=200,
            description="Test task",
            steps=(TaskStep(tool_name="read_file", tool_input={"path": "a.md"}),),
            schedule=Schedule(schedule_type=ScheduleType.once),
        )

        assert plan.status == TaskStatus.pending
        assert plan.created_at == ""
        assert plan.results == ()
        assert plan.current_iteration == 0
        assert plan.max_results_kept == 100
        assert plan.summarize_on_complete is True
        assert plan.progress_interval == 1
        assert plan.last_error == ""
        assert plan.consecutive_errors == 0
        assert plan.max_consecutive_errors == 5

    def test_replace_status(self):
        plan = TaskPlan(
            task_id="abc123",
            chat_id=100,
            user_id=200,
            description="Test task",
            steps=(TaskStep(tool_name="read_file", tool_input={"path": "a.md"}),),
            schedule=Schedule(schedule_type=ScheduleType.once),
        )

        updated = replace(plan, status=TaskStatus.running)

        assert plan.status == TaskStatus.pending
        assert updated.status == TaskStatus.running
        assert updated.task_id == plan.task_id

    def test_replace_results(self):
        plan = TaskPlan(
            task_id="abc123",
            chat_id=100,
            user_id=200,
            description="Test task",
            steps=(TaskStep(tool_name="read_file", tool_input={"path": "a.md"}),),
            schedule=Schedule(schedule_type=ScheduleType.once),
        )

        result = TaskResult(
            iteration=1,
            timestamp="2025-01-01T00:00:00+00:00",
            tool_name="read_file",
            tool_input={"path": "a.md"},
            content="file contents",
            is_error=False,
        )
        updated = replace(plan, results=(result,), current_iteration=1)

        assert len(updated.results) == 1
        assert updated.current_iteration == 1
        assert plan.results == ()

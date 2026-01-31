"""Tests for scheduler tools (Claude-facing interface)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from folderbot.scheduler.models import (
    Schedule,
    ScheduleType,
    TaskPlan,
    TaskResult,
    TaskStatus,
    TaskStep,
)
from folderbot.scheduler.tools import SchedulerTools


@pytest.fixture
def mock_scheduler() -> MagicMock:
    scheduler = MagicMock()
    scheduler.create_task = AsyncMock(return_value="abc123")
    scheduler.cancel_task = AsyncMock(return_value=True)
    scheduler.list_tasks = MagicMock(return_value=[])
    scheduler.get_task_results = MagicMock(return_value=None)
    return scheduler


@pytest.fixture
def tools(mock_scheduler: MagicMock) -> SchedulerTools:
    return SchedulerTools(mock_scheduler)


class TestGetToolDefinitions:
    def test_returns_four_tools(self, tools: SchedulerTools):
        defs = tools.get_tool_definitions()
        assert len(defs) == 4

    def test_tool_names(self, tools: SchedulerTools):
        defs = tools.get_tool_definitions()
        names = {d["name"] for d in defs}
        assert names == {
            "schedule_task",
            "list_tasks",
            "cancel_task",
            "get_task_results",
        }

    def test_tool_definitions_have_required_fields(self, tools: SchedulerTools):
        for tool_def in tools.get_tool_definitions():
            assert "name" in tool_def
            assert "description" in tool_def
            assert "input_schema" in tool_def


class TestExecuteRouting:
    async def test_unknown_tool_returns_none(self, tools: SchedulerTools):
        result = await tools.execute("unknown_tool", {}, chat_id=1, user_id=2)
        assert result is None

    async def test_routes_to_schedule_task(
        self, tools: SchedulerTools, mock_scheduler: MagicMock
    ):
        result = await tools.execute(
            "schedule_task",
            {
                "description": "Test task",
                "steps": [{"tool_name": "read_file", "tool_input": {"path": "a.md"}}],
                "schedule_type": "once",
            },
            chat_id=100,
            user_id=200,
        )

        assert result is not None
        assert not result.is_error
        assert "abc123" in result.content
        mock_scheduler.create_task.assert_called_once()

    async def test_routes_to_list_tasks(
        self, tools: SchedulerTools, mock_scheduler: MagicMock
    ):
        result = await tools.execute("list_tasks", {}, chat_id=100, user_id=200)

        assert result is not None
        assert "No scheduled tasks" in result.content
        mock_scheduler.list_tasks.assert_called_once_with(200, "")

    async def test_routes_to_cancel_task(
        self, tools: SchedulerTools, mock_scheduler: MagicMock
    ):
        result = await tools.execute(
            "cancel_task",
            {"task_id": "abc123"},
            chat_id=100,
            user_id=200,
        )

        assert result is not None
        assert "cancelled" in result.content
        mock_scheduler.cancel_task.assert_called_once_with("abc123", 200)

    async def test_routes_to_get_task_results(
        self, tools: SchedulerTools, mock_scheduler: MagicMock
    ):
        result = await tools.execute(
            "get_task_results",
            {"task_id": "abc123"},
            chat_id=100,
            user_id=200,
        )

        assert result is not None
        assert result.is_error  # Not found since mock returns None


class TestScheduleTask:
    async def test_invalid_schedule_type(self, tools: SchedulerTools):
        result = await tools.execute(
            "schedule_task",
            {
                "description": "Test",
                "steps": [{"tool_name": "read_file", "tool_input": {"path": "a.md"}}],
                "schedule_type": "invalid",
            },
            chat_id=100,
            user_id=200,
        )

        assert result is not None
        assert result.is_error
        assert "Invalid schedule_type" in result.content

    async def test_creates_correct_plan(
        self, tools: SchedulerTools, mock_scheduler: MagicMock
    ):
        await tools.execute(
            "schedule_task",
            {
                "description": "Check files",
                "steps": [
                    {"tool_name": "read_file", "tool_input": {"path": "a.md"}},
                    {"tool_name": "search_files", "tool_input": {"query": "test"}},
                ],
                "schedule_type": "repeating",
                "interval_seconds": 60,
                "max_iterations": 10,
                "summarize_on_complete": False,
                "progress_interval": 5,
            },
            chat_id=100,
            user_id=200,
        )

        plan = mock_scheduler.create_task.call_args[0][0]
        assert isinstance(plan, TaskPlan)
        assert plan.description == "Check files"
        assert len(plan.steps) == 2
        assert plan.schedule.schedule_type == ScheduleType.repeating
        assert plan.schedule.interval_seconds == 60
        assert plan.schedule.max_iterations == 10
        assert plan.summarize_on_complete is False
        assert plan.progress_interval == 5
        assert plan.chat_id == 100
        assert plan.user_id == 200

    async def test_schedule_description_in_response(
        self,
        tools: SchedulerTools,
    ):
        result = await tools.execute(
            "schedule_task",
            {
                "description": "Test task",
                "steps": [{"tool_name": "read_file", "tool_input": {"path": "a.md"}}],
                "schedule_type": "time_limited",
                "duration_seconds": 300,
                "interval_seconds": 5,
            },
            chat_id=100,
            user_id=200,
        )

        assert result is not None
        assert "300s" in result.content
        assert "5s" in result.content


class TestListTasks:
    async def test_empty_list(self, tools: SchedulerTools):
        result = await tools.execute("list_tasks", {}, chat_id=100, user_id=200)

        assert result is not None
        assert "No scheduled tasks" in result.content

    async def test_with_tasks(self, tools: SchedulerTools, mock_scheduler: MagicMock):
        mock_scheduler.list_tasks.return_value = [
            TaskPlan(
                task_id="t1",
                chat_id=100,
                user_id=200,
                description="Read files hourly",
                steps=(TaskStep(tool_name="read_file", tool_input={"path": "a.md"}),),
                schedule=Schedule(
                    schedule_type=ScheduleType.repeating,
                    interval_seconds=3600,
                ),
                status=TaskStatus.running,
                current_iteration=5,
                created_at="2025-01-01T00:00:00+00:00",
            ),
        ]

        result = await tools.execute("list_tasks", {}, chat_id=100, user_id=200)

        assert result is not None
        assert "t1" in result.content
        assert "Read files hourly" in result.content
        assert "running" in result.content

    async def test_status_filter(
        self, tools: SchedulerTools, mock_scheduler: MagicMock
    ):
        await tools.execute(
            "list_tasks",
            {"status_filter": "running"},
            chat_id=100,
            user_id=200,
        )

        mock_scheduler.list_tasks.assert_called_once_with(200, "running")


class TestCancelTask:
    async def test_cancel_success(
        self, tools: SchedulerTools, mock_scheduler: MagicMock
    ):
        result = await tools.execute(
            "cancel_task",
            {"task_id": "abc123"},
            chat_id=100,
            user_id=200,
        )

        assert result is not None
        assert not result.is_error
        assert "cancelled" in result.content

    async def test_cancel_not_found(
        self, tools: SchedulerTools, mock_scheduler: MagicMock
    ):
        mock_scheduler.cancel_task.return_value = False

        result = await tools.execute(
            "cancel_task",
            {"task_id": "nonexistent"},
            chat_id=100,
            user_id=200,
        )

        assert result is not None
        assert result.is_error
        assert "not found" in result.content


class TestGetTaskResults:
    async def test_not_found(self, tools: SchedulerTools):
        result = await tools.execute(
            "get_task_results",
            {"task_id": "nonexistent"},
            chat_id=100,
            user_id=200,
        )

        assert result is not None
        assert result.is_error

    async def test_with_results(self, tools: SchedulerTools, mock_scheduler: MagicMock):
        mock_scheduler.get_task_results.return_value = TaskPlan(
            task_id="t1",
            chat_id=100,
            user_id=200,
            description="Test task",
            steps=(TaskStep(tool_name="read_file", tool_input={"path": "a.md"}),),
            schedule=Schedule(schedule_type=ScheduleType.once),
            status=TaskStatus.completed,
            current_iteration=3,
            results=(
                TaskResult(
                    iteration=1,
                    timestamp="2025-01-01T00:00:00+00:00",
                    tool_name="read_file",
                    tool_input={"path": "a.md"},
                    content="file contents iter 1",
                    is_error=False,
                ),
                TaskResult(
                    iteration=2,
                    timestamp="2025-01-01T00:01:00+00:00",
                    tool_name="read_file",
                    tool_input={"path": "a.md"},
                    content="file contents iter 2",
                    is_error=False,
                ),
            ),
            created_at="2025-01-01T00:00:00+00:00",
        )

        result = await tools.execute(
            "get_task_results",
            {"task_id": "t1"},
            chat_id=100,
            user_id=200,
        )

        assert result is not None
        assert not result.is_error
        assert "Test task" in result.content
        assert "completed" in result.content
        assert "file contents iter 1" in result.content


class TestDescribeSchedule:
    def test_once_immediate(self):
        schedule = Schedule(schedule_type=ScheduleType.once)
        desc = SchedulerTools._describe_schedule(schedule)
        assert desc == "once immediately"

    def test_once_with_delay(self):
        schedule = Schedule(schedule_type=ScheduleType.once, delay_seconds=30)
        desc = SchedulerTools._describe_schedule(schedule)
        assert "30s delay" in desc

    def test_repeating(self):
        schedule = Schedule(
            schedule_type=ScheduleType.repeating,
            interval_seconds=60,
        )
        desc = SchedulerTools._describe_schedule(schedule)
        assert "every 60s" in desc

    def test_repeating_with_max(self):
        schedule = Schedule(
            schedule_type=ScheduleType.repeating,
            interval_seconds=60,
            max_iterations=10,
        )
        desc = SchedulerTools._describe_schedule(schedule)
        assert "max 10" in desc

    def test_cron(self):
        schedule = Schedule(
            schedule_type=ScheduleType.cron,
            cron_expression="0 9 * * *",
        )
        desc = SchedulerTools._describe_schedule(schedule)
        assert "0 9 * * *" in desc

    def test_time_limited(self):
        schedule = Schedule(
            schedule_type=ScheduleType.time_limited,
            duration_seconds=300,
            interval_seconds=5,
        )
        desc = SchedulerTools._describe_schedule(schedule)
        assert "300s" in desc
        assert "5s" in desc

"""Scheduler tools that Claude can use to create and manage tasks."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from pydantic import Field
from pydantic.dataclasses import dataclass

from ..tools.base import ToolDefinition, ToolResult
from .models import (
    Schedule,
    ScheduleType,
    TaskPlan,
    TaskStep,
)

if TYPE_CHECKING:
    from .scheduler import TaskScheduler


@dataclass(frozen=True)
class TaskStepInput:
    """A single tool call within a task."""

    tool_name: str = Field(
        description=(
            "Name of the tool to call (e.g., 'search_files', 'read_file', "
            "or any custom tool)"
        )
    )
    tool_input: dict[str, Any] = Field(
        description="Input parameters for the tool, matching the tool's input schema"
    )


@dataclass(frozen=True)
class ScheduleTaskInput:
    """Input for scheduling a new task."""

    description: str = Field(
        description="Human-readable description of what this task does and why"
    )
    steps: list[TaskStepInput] = Field(
        description=(
            "List of tool calls to execute each iteration. Usually one step, "
            "but can be multiple for multi-step tasks."
        )
    )
    schedule_type: str = Field(
        description=(
            "Type of schedule: 'once' (run once after delay), "
            "'repeating' (run at intervals), 'cron' (cron expression), "
            "'time_limited' (run until time expires)"
        )
    )
    delay_seconds: int = Field(
        default=0,
        description=(
            "For 'once': seconds to wait before executing. "
            "For 'repeating': initial delay before first execution."
        ),
    )
    interval_seconds: int = Field(
        default=0,
        description=(
            "For 'repeating': seconds between executions. "
            "For 'time_limited': seconds between iterations."
        ),
    )
    cron_expression: str = Field(
        default="",
        description=(
            "For 'cron': standard cron expression (e.g., '0 9 * * *' for daily at 9am)"
        ),
    )
    duration_seconds: int = Field(
        default=0,
        description="For 'time_limited': maximum total duration in seconds",
    )
    max_iterations: int = Field(
        default=0,
        description="Maximum number of iterations. 0 = unlimited (within schedule constraints)",
    )
    summarize_on_complete: bool = Field(
        default=True,
        description="Whether to generate a Claude summary when the task completes",
    )
    progress_interval: int = Field(
        default=1,
        description=(
            "Send progress update every N iterations. "
            "Set higher for fast-running tasks."
        ),
    )


@dataclass(frozen=True)
class ListTasksInput:
    """Input for listing scheduled tasks."""

    status_filter: str = Field(
        default="",
        description=(
            "Filter by status: 'pending', 'running', 'completed', "
            "'cancelled', 'failed', 'active' (pending+running), "
            "'done' (completed+cancelled+failed). Empty for all."
        ),
    )


@dataclass(frozen=True)
class CancelTaskInput:
    """Input for cancelling a scheduled task."""

    task_id: str = Field(description="ID of the task to cancel")


@dataclass(frozen=True)
class GetTaskResultsInput:
    """Input for getting results of a task."""

    task_id: str = Field(description="ID of the task to get results for")
    last_n: int = Field(
        default=10,
        description="Number of most recent results to return",
    )


SCHEDULER_TOOL_DEFINITIONS = [
    ToolDefinition(
        name="schedule_task",
        description=(
            "Schedule a task to be executed later or repeatedly. The task will run "
            "the specified tool(s) on the given schedule and report progress via "
            "Telegram messages. Use this for: delayed execution ('check this in 30 min'), "
            "repeating tasks ('check every hour'), cron tasks ('daily at 9am'), or "
            "time-limited bursts ('try for 5 minutes')."
        ),
        input_model=ScheduleTaskInput,
    ),
    ToolDefinition(
        name="list_tasks",
        description=(
            "List all scheduled tasks, optionally filtered by status. Shows task ID, "
            "description, schedule, status, and iteration count."
        ),
        input_model=ListTasksInput,
    ),
    ToolDefinition(
        name="cancel_task",
        description="Cancel a running or pending scheduled task.",
        input_model=CancelTaskInput,
    ),
    ToolDefinition(
        name="get_task_results",
        description=(
            "Get the results of a scheduled task. Returns the most recent execution "
            "results. Useful for checking what a task has found so far."
        ),
        input_model=GetTaskResultsInput,
    ),
]


class SchedulerTools:
    """Tools for Claude to interact with the task scheduler."""

    def __init__(self, scheduler: TaskScheduler):
        self._scheduler = scheduler

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions for the API."""
        return [t.to_api_format() for t in SCHEDULER_TOOL_DEFINITIONS]

    async def execute(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        chat_id: int,
        user_id: int,
    ) -> ToolResult | None:
        """Execute a scheduler tool. Returns None if tool not found."""
        handlers: dict[str, Any] = {
            "schedule_task": self._schedule_task,
            "list_tasks": self._list_tasks,
            "cancel_task": self._cancel_task,
            "get_task_results": self._get_task_results,
        }
        handler = handlers.get(tool_name)
        if handler:
            return await handler(tool_input, chat_id, user_id)
        return None

    async def _schedule_task(
        self, tool_input: dict[str, Any], chat_id: int, user_id: int
    ) -> ToolResult:
        params = ScheduleTaskInput(**tool_input)

        try:
            schedule_type = ScheduleType(params.schedule_type)
        except ValueError:
            return ToolResult(
                content=f"Invalid schedule_type: {params.schedule_type}. "
                f"Must be one of: once, repeating, cron, time_limited",
                is_error=True,
            )

        steps = tuple(
            TaskStep(tool_name=s.tool_name, tool_input=s.tool_input)
            for s in params.steps
        )
        schedule = Schedule(
            schedule_type=schedule_type,
            delay_seconds=params.delay_seconds,
            interval_seconds=params.interval_seconds,
            cron_expression=params.cron_expression,
            duration_seconds=params.duration_seconds,
            max_iterations=params.max_iterations,
        )

        # Compute next_run_at (absolute timestamp) based on schedule type
        now = datetime.now(timezone.utc)
        next_run_at = ""
        deadline_at = ""

        if schedule_type == ScheduleType.once:
            next_run_at = (now + timedelta(seconds=params.delay_seconds)).isoformat()

        elif schedule_type == ScheduleType.repeating:
            # Initial delay before first execution
            next_run_at = (now + timedelta(seconds=params.delay_seconds)).isoformat()

        elif schedule_type == ScheduleType.cron:
            # Compute next cron run time
            next_run_at = self._next_cron_time(params.cron_expression).isoformat()

        elif schedule_type == ScheduleType.time_limited:
            # Start immediately, set deadline
            next_run_at = now.isoformat()
            deadline_at = (now + timedelta(seconds=params.duration_seconds)).isoformat()

        plan = TaskPlan(
            task_id=uuid.uuid4().hex[:12],
            chat_id=chat_id,
            user_id=user_id,
            description=params.description,
            steps=steps,
            schedule=schedule,
            created_at=now.isoformat(),
            next_run_at=next_run_at,
            deadline_at=deadline_at,
            summarize_on_complete=params.summarize_on_complete,
            progress_interval=params.progress_interval,
        )

        task_id = await self._scheduler.create_task(plan)
        schedule_desc = self._describe_schedule(schedule)
        return ToolResult(
            content=f"Task scheduled: {plan.description}\n"
            f"ID: {task_id}\n"
            f"Schedule: {schedule_desc}\n"
            f"Steps: {len(steps)} tool call(s) per iteration"
        )

    async def _list_tasks(
        self, tool_input: dict[str, Any], chat_id: int, user_id: int
    ) -> ToolResult:
        params = ListTasksInput(**tool_input)
        tasks = self._scheduler.list_tasks(user_id, params.status_filter)

        if not tasks:
            return ToolResult(content="No scheduled tasks found.")

        lines = []
        for t in tasks[:20]:
            schedule_desc = self._describe_schedule(t.schedule)
            lines.append(
                f"- [{t.task_id}] {t.description}\n"
                f"  Status: {t.status.value} | Iterations: {t.current_iteration} | "
                f"Schedule: {schedule_desc}"
            )
        return ToolResult(content="\n".join(lines))

    async def _cancel_task(
        self, tool_input: dict[str, Any], chat_id: int, user_id: int
    ) -> ToolResult:
        params = CancelTaskInput(**tool_input)
        cancelled = await self._scheduler.cancel_task(params.task_id, user_id)
        if cancelled:
            return ToolResult(content=f"Task {params.task_id} cancelled.")
        return ToolResult(
            content=f"Task {params.task_id} not found or not owned by you.",
            is_error=True,
        )

    async def _get_task_results(
        self, tool_input: dict[str, Any], chat_id: int, user_id: int
    ) -> ToolResult:
        params = GetTaskResultsInput(**tool_input)
        plan = self._scheduler.get_task_results(params.task_id, user_id)
        if plan is None:
            return ToolResult(
                content=f"Task {params.task_id} not found or not owned by you.",
                is_error=True,
            )

        lines = [
            f"Task: {plan.description}",
            f"Status: {plan.status.value}",
            f"Iterations: {plan.current_iteration}",
            "",
            f"Last {params.last_n} results:",
        ]
        for r in plan.results[-params.last_n :]:
            status = "ERROR" if r.is_error else "OK"
            content_preview = (
                r.content[:300] + "..." if len(r.content) > 300 else r.content
            )
            lines.append(
                f"  [{r.iteration}] {r.tool_name} ({status}): {content_preview}"
            )

        return ToolResult(content="\n".join(lines))

    @staticmethod
    def _describe_schedule(schedule: Schedule) -> str:
        """Human-readable schedule description."""
        st = schedule.schedule_type
        if st == ScheduleType.once:
            if schedule.delay_seconds > 0:
                return f"once after {schedule.delay_seconds}s delay"
            return "once immediately"
        if st == ScheduleType.repeating:
            parts = f"every {schedule.interval_seconds}s"
            if schedule.max_iterations > 0:
                parts += f" (max {schedule.max_iterations} iterations)"
            return parts
        if st == ScheduleType.cron:
            return f"cron: {schedule.cron_expression}"
        if st == ScheduleType.time_limited:
            return (
                f"for {schedule.duration_seconds}s, every {schedule.interval_seconds}s"
            )
        return str(st)

    @staticmethod
    def _next_cron_time(expression: str) -> datetime:
        """Calculate next run time from a cron expression."""
        from croniter import croniter

        cron = croniter(expression, datetime.now(timezone.utc))
        return cron.get_next(datetime)  # type: ignore[return-value]

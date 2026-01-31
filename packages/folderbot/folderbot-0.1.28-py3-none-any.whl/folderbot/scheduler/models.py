"""Data models for the task scheduler."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ScheduleType(str, Enum):
    """Type of task schedule."""

    immediate = "immediate"  # Execute now, synchronously (for unified tool execution)
    once = "once"
    repeating = "repeating"
    cron = "cron"
    time_limited = "time_limited"


class TaskStatus(str, Enum):
    """Current status of a scheduled task."""

    pending = "pending"
    running = "running"
    completed = "completed"
    cancelled = "cancelled"
    failed = "failed"


@dataclass(frozen=True)
class TaskStep:
    """A single tool invocation within a task plan."""

    tool_name: str
    tool_input: dict[str, Any]


@dataclass(frozen=True)
class Schedule:
    """Schedule configuration for a task."""

    schedule_type: ScheduleType
    delay_seconds: int = 0
    interval_seconds: int = 0
    cron_expression: str = ""
    duration_seconds: int = 0
    max_iterations: int = 0


@dataclass(frozen=True)
class TaskResult:
    """Result of a single task execution."""

    iteration: int
    timestamp: str
    tool_name: str
    tool_input: dict[str, Any]
    content: str
    is_error: bool


@dataclass(frozen=True)
class TaskPlan:
    """A complete task plan created by Claude."""

    task_id: str
    chat_id: int
    user_id: int
    description: str
    steps: tuple[TaskStep, ...]
    schedule: Schedule
    status: TaskStatus = TaskStatus.pending
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    next_run_at: str = ""  # ISO timestamp of next scheduled execution
    deadline_at: str = ""  # ISO timestamp for time-limited task deadlines
    results: tuple[TaskResult, ...] = ()
    current_iteration: int = 0
    max_results_kept: int = 100
    summarize_on_complete: bool = True
    progress_interval: int = 1
    last_error: str = ""
    consecutive_errors: int = 0
    max_consecutive_errors: int = 5

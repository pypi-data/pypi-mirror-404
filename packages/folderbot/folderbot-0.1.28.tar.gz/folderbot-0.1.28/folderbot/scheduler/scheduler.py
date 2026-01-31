"""Core task scheduler engine."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from croniter import croniter

from ..prompts import get_task_summary_prompt
from ..tools.base import ToolResult
from .models import (
    ScheduleType,
    TaskPlan,
    TaskResult,
    TaskStatus,
)
from .persistence import TaskStore

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from ..tools.folder_tools import FolderTools

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Manages scheduled task lifecycle and execution via heartbeat polling."""

    HEARTBEAT_INTERVAL = 1  # seconds between heartbeat checks

    def __init__(
        self,
        task_store: TaskStore,
        send_message: Callable[[int, str], Awaitable[None]],
        summarize: Callable[[str, int], Awaitable[str]],
    ):
        self._folder_tools: FolderTools | None = None
        self._store = task_store
        self._send_message = send_message
        self._summarize = summarize
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._task_plans: dict[str, TaskPlan] = {}

    def set_folder_tools(self, folder_tools: FolderTools) -> None:
        """Set the folder tools reference (called after construction)."""
        self._folder_tools = folder_tools

    async def start(self) -> None:
        """Initialize scheduler, restore persisted tasks, start heartbeat."""
        persisted = self._store.load_active_tasks()
        for plan in persisted:
            # Keep the task as-is (preserving next_run_at), just ensure status is pending
            restored = replace(plan, status=TaskStatus.pending)
            self._task_plans[plan.task_id] = restored
            logger.info(f"Restored task {plan.task_id}: {plan.description}")

        # Start the single heartbeat loop
        self._heartbeat_task = asyncio.create_task(self._heartbeat())

    async def shutdown(self) -> None:
        """Gracefully stop the heartbeat and save all tasks."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        for plan in self._task_plans.values():
            self._store.save_task(plan)

    async def create_task(self, plan: TaskPlan) -> str:
        """Register a new task. Returns task_id. Heartbeat will execute it."""
        self._task_plans[plan.task_id] = plan
        self._store.save_task(plan)
        logger.info(f"Created task {plan.task_id}: {plan.description}")

        # Log to activity log
        if self._folder_tools:
            self._folder_tools.activity_logger.log_task_event(
                event="scheduled",
                task_id=plan.task_id,
                description=plan.description,
                user_id=plan.user_id,
                details={"schedule_type": plan.schedule.schedule_type.value},
            )

        return plan.task_id

    async def execute_immediate(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        user_id: int = 0,
    ) -> ToolResult:
        """Execute a tool immediately through the scheduler (unified execution path).

        This allows all tool calls to go through the scheduler for consistent
        logging, monitoring, and potential safeguards.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Tool input parameters
            user_id: User ID for logging

        Returns:
            ToolResult from the tool execution
        """
        if self._folder_tools is None:
            return ToolResult(
                content="Scheduler not initialized with folder tools",
                is_error=True,
            )

        # Execute the tool directly (no task plan needed for immediate)
        try:
            result = self._folder_tools.execute_direct(
                tool_name, tool_input, user_id=user_id
            )
            return result
        except Exception as e:
            logger.exception(f"Immediate tool execution failed: {tool_name}")
            return ToolResult(content=f"Execution error: {e}", is_error=True)

    # Map common aliases to actual status values
    _STATUS_ALIASES: dict[str, set[str]] = {
        "active": {"pending", "running"},
        "done": {"completed", "cancelled", "failed"},
        "finished": {"completed", "cancelled", "failed"},
    }

    def list_tasks(self, user_id: int, status_filter: str = "") -> list[TaskPlan]:
        """List tasks for a user, optionally filtered by status."""
        # Merge in-memory state (most up-to-date) with persisted tasks
        # so that completed/failed/cancelled tasks survive restarts
        persisted = self._store.load_user_tasks(user_id)
        merged: dict[str, TaskPlan] = {p.task_id: p for p in persisted}
        for plan in self._task_plans.values():
            if plan.user_id == user_id:
                merged[plan.task_id] = plan  # in-memory wins
        tasks = list(merged.values())
        if status_filter:
            # Support aliases like "active" -> pending + running
            allowed = self._STATUS_ALIASES.get(status_filter, {status_filter})
            tasks = [t for t in tasks if t.status.value in allowed]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    async def cancel_task(self, task_id: str, user_id: int) -> bool:
        """Cancel a task. Returns True if found and cancelled."""
        plan = self._task_plans.get(task_id)
        if not plan or plan.user_id != user_id:
            return False

        updated = replace(
            plan,
            status=TaskStatus.cancelled,
            completed_at=datetime.now(timezone.utc).isoformat(),
            next_run_at="",  # Clear scheduled run
        )
        self._task_plans[task_id] = updated
        self._store.save_task(updated)
        logger.info(f"Cancelled task {task_id}: {plan.description}")

        # Log to activity log
        if self._folder_tools:
            self._folder_tools.activity_logger.log_task_event(
                event="cancelled",
                task_id=task_id,
                description=plan.description,
                user_id=user_id,
            )

        return True

    def get_task_results(self, task_id: str, user_id: int) -> TaskPlan | None:
        """Get task plan with results. Returns None if not found/unauthorized."""
        plan = self._task_plans.get(task_id)
        if not plan or plan.user_id != user_id:
            return None
        return plan

    async def _heartbeat(self) -> None:
        """Main heartbeat loop that polls for tasks ready to execute."""
        while True:
            now = datetime.now(timezone.utc)

            for task_id, plan in list(self._task_plans.items()):
                # Skip tasks that aren't active
                if plan.status not in (TaskStatus.pending, TaskStatus.running):
                    continue

                # Skip tasks without a scheduled run time
                if not plan.next_run_at:
                    continue

                # Check if it's time to run
                next_run = datetime.fromisoformat(plan.next_run_at)
                if next_run <= now:
                    try:
                        await self._execute_iteration(task_id)
                        # Advance schedule (may complete the task)
                        await self._advance_schedule(task_id)
                    except Exception as e:
                        logger.exception(f"Task {task_id} failed with unexpected error")
                        plan = self._task_plans[task_id]
                        updated = replace(
                            plan,
                            status=TaskStatus.failed,
                            last_error=str(e),
                            completed_at=now.isoformat(),
                            next_run_at="",
                        )
                        self._task_plans[task_id] = updated
                        self._store.save_task(updated)

                        # Log to activity log
                        if self._folder_tools:
                            self._folder_tools.activity_logger.log_task_event(
                                event="failed",
                                task_id=task_id,
                                description=plan.description,
                                user_id=plan.user_id,
                                details={"error": str(e)},
                            )

                        await self._send_message(
                            plan.chat_id,
                            f"Task failed: {plan.description}\nError: {e}",
                        )

            await asyncio.sleep(self.HEARTBEAT_INTERVAL)

    async def _advance_schedule(self, task_id: str) -> None:
        """Compute the next run time based on schedule type, or complete the task."""
        plan = self._task_plans[task_id]
        schedule = plan.schedule
        now = datetime.now(timezone.utc)

        # Check if task failed during execution
        if plan.status == TaskStatus.failed:
            return

        # Handle based on schedule type
        if schedule.schedule_type == ScheduleType.once:
            # One-off tasks complete after single execution
            await self._complete_task(task_id)
            return

        if schedule.schedule_type == ScheduleType.repeating:
            # Check max iterations
            if (
                schedule.max_iterations > 0
                and plan.current_iteration >= schedule.max_iterations
            ):
                await self._complete_task(task_id)
                return

            # Schedule next run
            next_run = now + timedelta(seconds=schedule.interval_seconds)
            updated = replace(plan, next_run_at=next_run.isoformat())
            self._task_plans[task_id] = updated
            self._store.save_task(updated)
            return

        if schedule.schedule_type == ScheduleType.cron:
            # Check max iterations
            if (
                schedule.max_iterations > 0
                and plan.current_iteration >= schedule.max_iterations
            ):
                await self._complete_task(task_id)
                return

            # Schedule next cron run
            next_run = self._next_cron_time(schedule.cron_expression)
            updated = replace(plan, next_run_at=next_run.isoformat())
            self._task_plans[task_id] = updated
            self._store.save_task(updated)
            return

        if schedule.schedule_type == ScheduleType.time_limited:
            # Check deadline
            if plan.deadline_at:
                deadline = datetime.fromisoformat(plan.deadline_at)
                if now >= deadline:
                    await self._complete_task(task_id)
                    return

            # Check max iterations
            if (
                schedule.max_iterations > 0
                and plan.current_iteration >= schedule.max_iterations
            ):
                await self._complete_task(task_id)
                return

            # Schedule next run (capped at deadline if set)
            interval = max(schedule.interval_seconds, 1)
            next_run = now + timedelta(seconds=interval)

            if plan.deadline_at:
                deadline = datetime.fromisoformat(plan.deadline_at)
                if next_run > deadline:
                    # Don't schedule past deadline; task will complete on next check
                    next_run = deadline

            updated = replace(plan, next_run_at=next_run.isoformat())
            self._task_plans[task_id] = updated
            self._store.save_task(updated)

    async def _execute_iteration(self, task_id: str) -> None:
        """Execute one iteration of a task (all steps in sequence)."""
        if self._folder_tools is None:
            logger.error(f"Task {task_id}: folder_tools not set")
            return

        plan = self._task_plans[task_id]
        iteration = plan.current_iteration + 1

        # Mark as running on first iteration
        if plan.status == TaskStatus.pending:
            plan = replace(
                plan,
                status=TaskStatus.running,
                started_at=datetime.now(timezone.utc).isoformat(),
            )

        results_this_iteration: list[TaskResult] = []

        for step in plan.steps:
            try:
                result = self._folder_tools.execute(step.tool_name, step.tool_input)
            except Exception as e:
                result = ToolResult(content=f"Execution error: {e}", is_error=True)

            task_result = TaskResult(
                iteration=iteration,
                timestamp=datetime.now(timezone.utc).isoformat(),
                tool_name=step.tool_name,
                tool_input=step.tool_input,
                content=result.content,
                is_error=result.is_error,
            )
            results_this_iteration.append(task_result)

            # send_message results go directly to the user
            if step.tool_name == "send_message" and not result.is_error:
                await self._send_message(plan.chat_id, result.content)

            if result.is_error:
                new_consecutive = plan.consecutive_errors + 1
                plan = replace(
                    plan,
                    consecutive_errors=new_consecutive,
                    last_error=result.content,
                )
                if new_consecutive >= plan.max_consecutive_errors:
                    plan = replace(
                        plan,
                        status=TaskStatus.failed,
                        completed_at=datetime.now(timezone.utc).isoformat(),
                    )
                    self._task_plans[task_id] = plan
                    self._store.save_task(plan)
                    await self._send_message(
                        plan.chat_id,
                        f"Task stopped after {plan.max_consecutive_errors} "
                        f"consecutive errors: {plan.description}\n"
                        f"Last error: {result.content}",
                    )
                    return
            else:
                plan = replace(plan, consecutive_errors=0, last_error="")

        # Update plan with new results (capped)
        all_results = plan.results + tuple(results_this_iteration)
        if len(all_results) > plan.max_results_kept:
            all_results = all_results[-plan.max_results_kept :]

        plan = replace(
            plan,
            current_iteration=iteration,
            results=all_results,
        )
        self._task_plans[task_id] = plan
        self._store.save_task(plan)

        # Send progress update if interval reached
        if plan.progress_interval > 0 and iteration % plan.progress_interval == 0:
            await self._send_progress(plan, results_this_iteration)

    async def _send_progress(
        self, plan: TaskPlan, latest_results: list[TaskResult]
    ) -> None:
        """Send a progress update to the Telegram chat."""
        # Skip progress for send_message-only iterations (already sent directly)
        non_message_results = [
            r for r in latest_results if r.tool_name != "send_message"
        ]
        if not non_message_results:
            return

        max_iters = plan.schedule.max_iterations
        iters_str = str(max_iters) if max_iters > 0 else "unlimited"

        lines = [
            f"Task progress: {plan.description}",
            f"Iteration {plan.current_iteration}/{iters_str}",
        ]

        for r in non_message_results:
            status = "error" if r.is_error else "ok"
            content_preview = (
                r.content[:200] + "..." if len(r.content) > 200 else r.content
            )
            lines.append(f"  [{status}] {r.tool_name}: {content_preview}")

        await self._send_message(plan.chat_id, "\n".join(lines))

    async def _complete_task(self, task_id: str) -> None:
        """Mark a task as complete and optionally generate summary."""
        plan = self._task_plans[task_id]
        updated = replace(
            plan,
            status=TaskStatus.completed,
            completed_at=datetime.now(timezone.utc).isoformat(),
            next_run_at="",  # Clear scheduled run
        )
        self._task_plans[task_id] = updated
        self._store.save_task(updated)

        # Log to activity log
        if self._folder_tools:
            self._folder_tools.activity_logger.log_task_event(
                event="completed",
                task_id=task_id,
                description=plan.description,
                user_id=plan.user_id,
                details={"iterations": plan.current_iteration},
            )

        if updated.summarize_on_complete and updated.results:
            await self._generate_summary(updated)
        else:
            await self._send_message(
                updated.chat_id,
                f"Task completed: {updated.description}\n"
                f"Iterations: {updated.current_iteration}",
            )

    async def _generate_summary(self, plan: TaskPlan) -> None:
        """Call Claude to summarize task results, then send to Telegram."""
        result_lines = []
        for r in plan.results[-50:]:
            status = "ERROR" if r.is_error else "OK"
            content = r.content[:500] + "..." if len(r.content) > 500 else r.content
            result_lines.append(
                f"[Iteration {r.iteration}] {r.tool_name} ({status}): {content}"
            )

        prompt = get_task_summary_prompt().format(
            description=plan.description,
            schedule_type=plan.schedule.schedule_type.value,
            current_iteration=plan.current_iteration,
            results="\n".join(result_lines),
        )

        try:
            summary = await self._summarize(prompt, plan.chat_id)
            await self._send_message(
                plan.chat_id,
                f"Task completed: {plan.description}\n\nSummary:\n{summary}",
            )
        except Exception as e:
            logger.exception(f"Failed to generate summary for task {plan.task_id}")
            await self._send_message(
                plan.chat_id,
                f"Task completed: {plan.description}\n"
                f"Iterations: {plan.current_iteration}\n"
                f"(Summary generation failed: {e})",
            )

    @staticmethod
    def _next_cron_time(expression: str) -> datetime:
        """Calculate next run time from a cron expression."""
        cron = croniter(expression, datetime.now(timezone.utc))
        return cron.get_next(datetime)  # type: ignore[return-value]

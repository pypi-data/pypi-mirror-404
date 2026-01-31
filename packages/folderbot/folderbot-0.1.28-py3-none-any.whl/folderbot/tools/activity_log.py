"""Activity logging with structured entries and rotation."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class ReadActivityLogInput:
    """Input for reading the activity log."""

    last_n: int = Field(
        default=20,
        description="Number of recent entries to return (default 20, max 100)",
    )
    tool_filter: str = Field(
        default="",
        description="Filter entries by tool name (e.g., 'write_file', 'schedule_task')",
    )
    date: str = Field(
        default="",
        description="Filter by date in YYYY-MM-DD format (default: today)",
    )
    search: str = Field(
        default="",
        description="Search text in tool inputs/outputs (case-insensitive)",
    )


class ActivityLogger:
    """Logs tool activity to structured JSON files with rotation."""

    MAX_DAYS_TO_KEEP = 30

    def __init__(self, root_folder: Path):
        self._log_dir = root_folder / ".folderbot" / "logs"
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._rotate_old_logs()

    def _get_log_file(self, date: datetime | None = None) -> Path:
        """Get log file path for a given date."""
        if date is None:
            date = datetime.now()
        return self._log_dir / f"{date.strftime('%Y-%m-%d')}.jsonl"

    def _rotate_old_logs(self) -> None:
        """Delete logs older than MAX_DAYS_TO_KEEP."""
        cutoff = datetime.now() - timedelta(days=self.MAX_DAYS_TO_KEEP)
        for log_file in self._log_dir.glob("*.jsonl"):
            try:
                # Parse date from filename
                date_str = log_file.stem  # e.g., "2026-01-29"
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date < cutoff:
                    log_file.unlink()
            except (ValueError, OSError):
                pass  # Skip files that don't match expected format

    def log_tool_call(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        result: str,
        is_error: bool,
        user_id: int,
        duration_ms: int = 0,
    ) -> None:
        """Log a tool call with structured data."""
        entry = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "type": "tool_call",
            "tool": tool_name,
            "input": self._truncate_dict(tool_input),
            "result": self._truncate_str(result, 500),
            "error": is_error,
            "user_id": user_id,
            "duration_ms": duration_ms,
        }
        self._write_entry(entry)

    def log_message(
        self,
        direction: str,  # "user" or "assistant"
        content: str,
        user_id: int,
        tools_used: list[str] | None = None,
    ) -> None:
        """Log a message exchange."""
        entry = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "type": "message",
            "direction": direction,
            "content": self._truncate_str(content, 200),
            "user_id": user_id,
        }
        if tools_used:
            entry["tools_used"] = tools_used
        self._write_entry(entry)

    def log_task_event(
        self,
        event: str,  # "scheduled", "started", "completed", "failed", "cancelled"
        task_id: str,
        description: str,
        user_id: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Log a scheduler task event."""
        entry = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "type": "task_event",
            "event": event,
            "task_id": task_id,
            "description": self._truncate_str(description, 100),
            "user_id": user_id,
        }
        if details:
            entry["details"] = self._truncate_dict(details)
        self._write_entry(entry)

    def _write_entry(self, entry: dict[str, Any]) -> None:
        """Write an entry to the current day's log file."""
        log_file = self._get_log_file()
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _truncate_str(self, s: str, max_len: int) -> str:
        """Truncate string for logging."""
        if len(s) > max_len:
            return s[: max_len - 3] + "..."
        return s

    def _truncate_dict(
        self, d: dict[str, Any], max_str_len: int = 200
    ) -> dict[str, Any]:
        """Truncate string values in a dict for logging."""
        result: dict[str, Any] = {}
        for k, v in d.items():
            if isinstance(v, str):
                result[k] = self._truncate_str(v, max_str_len)
            elif isinstance(v, dict):
                result[k] = self._truncate_dict(v, max_str_len)
            elif isinstance(v, list):
                result[k] = [
                    self._truncate_str(str(item), max_str_len)
                    if isinstance(item, str)
                    else item
                    for item in v[:10]  # Limit list items
                ]
            else:
                result[k] = v
        return result

    def read_log(
        self,
        last_n: int = 20,
        tool_filter: str = "",
        date: str = "",
        search: str = "",
    ) -> str:
        """Read and filter log entries, returning human-readable format."""
        last_n = min(last_n, 100)  # Cap at 100

        # Determine which log file(s) to read
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
                log_files = [self._get_log_file(target_date)]
            except ValueError:
                return f"Invalid date format: {date}. Use YYYY-MM-DD."
        else:
            # Today's log
            log_files = [self._get_log_file()]

        # Read entries
        entries: list[dict[str, Any]] = []
        for log_file in log_files:
            if not log_file.exists():
                continue
            with open(log_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue

        # Apply filters
        if tool_filter:
            tool_filter_lower = tool_filter.lower()
            entries = [
                e
                for e in entries
                if e.get("type") == "tool_call"
                and tool_filter_lower in e.get("tool", "").lower()
            ]

        if search:
            search_lower = search.lower()
            filtered = []
            for e in entries:
                # Search in various fields
                searchable = json.dumps(e, ensure_ascii=False).lower()
                if search_lower in searchable:
                    filtered.append(e)
            entries = filtered

        # Take last N entries
        entries = entries[-last_n:]

        if not entries:
            filters_desc = []
            if tool_filter:
                filters_desc.append(f"tool={tool_filter}")
            if date:
                filters_desc.append(f"date={date}")
            if search:
                filters_desc.append(f"search={search}")
            filter_str = (
                f" (filters: {', '.join(filters_desc)})" if filters_desc else ""
            )
            return f"No log entries found{filter_str}."

        # Format output
        lines = [f"Activity log ({len(entries)} entries):\n"]
        for entry in entries:
            lines.append(self._format_entry(entry))

        return "\n".join(lines)

    def _format_entry(self, entry: dict[str, Any]) -> str:
        """Format a log entry for human reading."""
        ts = entry.get("ts", "")
        # Extract just time for readability
        time_str = ts[11:19] if len(ts) >= 19 else ts

        entry_type = entry.get("type", "unknown")

        if entry_type == "tool_call":
            tool = entry.get("tool", "?")
            is_error = entry.get("error", False)
            status = "❌" if is_error else "✓"
            duration = entry.get("duration_ms", 0)
            duration_str = f" ({duration}ms)" if duration else ""

            # Summarize input
            tool_input = entry.get("input", {})
            input_summary = self._summarize_input(tool_input)

            result = entry.get("result", "")
            result_preview = result[:80] + "..." if len(result) > 80 else result

            return f"[{time_str}] {status} {tool}{duration_str}\n  Input: {input_summary}\n  Result: {result_preview}"

        elif entry_type == "message":
            direction = entry.get("direction", "?")
            content = entry.get("content", "")
            tools = entry.get("tools_used", [])
            tools_str = f" [tools: {', '.join(tools)}]" if tools else ""
            icon = "👤" if direction == "user" else "🤖"
            return f"[{time_str}] {icon} {direction}{tools_str}: {content}"

        elif entry_type == "task_event":
            event = entry.get("event", "?")
            task_id = entry.get("task_id", "?")[:8]  # Short ID
            desc = entry.get("description", "")
            return f"[{time_str}] 📋 Task {event}: {task_id}... - {desc}"

        else:
            return f"[{time_str}] {entry}"

    def _summarize_input(self, tool_input: dict[str, Any]) -> str:
        """Create a brief summary of tool input."""
        parts = []
        for k, v in tool_input.items():
            if isinstance(v, str):
                v_str = v[:50] + "..." if len(v) > 50 else v
            elif isinstance(v, list):
                v_str = f"[{len(v)} items]"
            elif isinstance(v, dict):
                v_str = f"{{{len(v)} keys}}"
            else:
                v_str = str(v)
            parts.append(f"{k}={v_str}")
        return ", ".join(parts) if parts else "(none)"

    def get_available_dates(self) -> list[str]:
        """Return list of dates that have log files."""
        dates = []
        for log_file in sorted(self._log_dir.glob("*.jsonl")):
            dates.append(log_file.stem)
        return dates

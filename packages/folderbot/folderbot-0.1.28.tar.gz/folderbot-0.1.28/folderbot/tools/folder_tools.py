"""FolderTools class for interacting with the configured folder."""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pathspec

from ..config import Config
from .activity_log import ActivityLogger, ReadActivityLogInput
from .base import ToolDefinition, ToolResult
from .file_notifications import (
    DisableFileNotificationsInput,
    EnableFileNotificationsInput,
    GetFileNotificationStatusInput,
)
from .list_files import ListFilesInput
from .loader import load_custom_tools
from .read_file import ReadFileInput
from .read_files import ReadFilesInput
from .search_files import SearchFilesInput
from .utils import UtilTools
from .web_tools import WebTools
from .write_file import WriteFileInput, WriteMode

if TYPE_CHECKING:
    from ..scheduler.tools import SchedulerTools
    from ..session_manager import SessionManager

logger = logging.getLogger(__name__)

TOOL_DEFINITIONS = [
    ToolDefinition(
        name="list_files",
        description=(
            "List files in the folder or a subfolder. Returns file paths "
            "relative to the root folder. Use this to discover what files "
            "are available before reading them."
        ),
        input_model=ListFilesInput,
    ),
    ToolDefinition(
        name="read_file",
        description=(
            "Read the contents of a specific file. The path must be relative "
            "to the root folder. Use list_files first to discover available files."
        ),
        input_model=ReadFileInput,
    ),
    ToolDefinition(
        name="read_files",
        description=(
            "Read the contents of multiple files at once. Returns a concatenated "
            "view with file headers. Use this to read several related files together."
        ),
        input_model=ReadFilesInput,
    ),
    ToolDefinition(
        name="search_files",
        description=(
            "Search for text content across all files in the folder. "
            "Returns matching file paths and relevant excerpts. "
            "Useful for finding files containing specific keywords."
        ),
        input_model=SearchFilesInput,
    ),
    ToolDefinition(
        name="write_file",
        description=(
            "Create or update a file in the folder. The file path must "
            "satisfy the configured include rules. Use this to help the user "
            "manage their notes, todos, and documentation."
        ),
        input_model=WriteFileInput,
        requires_confirmation=True,  # Writing requires user confirmation
    ),
    ToolDefinition(
        name="read_activity_log",
        description=(
            "Read the bot's activity log to see what tools were actually used, "
            "when tasks were scheduled, and message history. Use this to verify "
            "whether actions were actually performed or to debug issues."
        ),
        input_model=ReadActivityLogInput,
    ),
    ToolDefinition(
        name="enable_file_notifications",
        description=(
            "Enable file change notifications. When enabled, the user will receive "
            "Telegram messages whenever files in the folder are created, modified, "
            "or deleted. Use this when the user wants to be notified about changes."
        ),
        input_model=EnableFileNotificationsInput,
    ),
    ToolDefinition(
        name="disable_file_notifications",
        description=(
            "Disable file change notifications. Use this when the user no longer "
            "wants to receive notifications about file changes."
        ),
        input_model=DisableFileNotificationsInput,
    ),
    ToolDefinition(
        name="get_file_notification_status",
        description=(
            "Check if file change notifications are currently enabled or disabled "
            "for the user."
        ),
        input_model=GetFileNotificationStatusInput,
    ),
]


class FolderTools:
    """Tools for interacting with the configured folder."""

    MAX_FILE_READ_CHARS = 50_000
    MAX_LIST_FILES = 100
    MAX_SEARCH_RESULTS = 10

    def __init__(
        self,
        config: Config,
        scheduler_tools: SchedulerTools | None = None,
    ):
        self.config = config
        self._root = config.root_folder.resolve()
        self._util_tools = UtilTools()
        self._web_tools = WebTools()
        self._scheduler_tools = scheduler_tools
        self._scheduler: Any = None  # TaskScheduler, set later to avoid circular dep
        self._session_manager: SessionManager | None = None  # Set later
        self._custom_tools = load_custom_tools(self._root)
        self._activity_logger = ActivityLogger(self._root)
        if self._custom_tools:
            logger.info("Custom tools loaded from .folderbot/tools")
        if self._web_tools.is_available():
            logger.info("Web tools available")

    def set_scheduler(self, scheduler: Any) -> None:
        """Set the scheduler reference for unified tool execution."""
        self._scheduler = scheduler

    def set_session_manager(self, session_manager: SessionManager) -> None:
        """Set the session manager reference for user preferences."""
        self._session_manager = session_manager

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Return tool definitions for the Claude API."""
        definitions = [tool.to_api_format() for tool in TOOL_DEFINITIONS]

        # Add utility tools
        definitions.extend(self._util_tools.get_tool_definitions())

        # Add web tools if available
        definitions.extend(self._web_tools.get_tool_definitions())

        # Add scheduler tools if available
        if self._scheduler_tools:
            definitions.extend(self._scheduler_tools.get_tool_definitions())

        # Add custom tool definitions if available
        if self._custom_tools:
            custom_defs = self._custom_tools.get_tool_definitions()
            definitions.extend(custom_defs)

        return definitions

    def get_tools_requiring_confirmation(self) -> list[str]:
        """Return names of tools that require user confirmation before use."""
        return [t.name for t in TOOL_DEFINITIONS if t.requires_confirmation]

    def _validate_path(self, relative_path: str) -> Path | None:
        """Validate and resolve a path, ensuring it's within root_folder.

        Returns the resolved absolute path if valid, None if path traversal detected.
        """
        if not relative_path:
            return self._root

        # Normalize the path
        clean_path = Path(relative_path).as_posix()

        # Reject obvious traversal attempts
        if ".." in clean_path or clean_path.startswith("/"):
            return None

        # Resolve to absolute path
        absolute_path = (self._root / clean_path).resolve()

        # Verify it's still within root
        try:
            absolute_path.relative_to(self._root)
            return absolute_path
        except ValueError:
            return None

    def _is_file_allowed(self, rel_path: str) -> bool:
        """Check if a file matches include patterns and not exclude patterns."""
        include_spec = pathspec.PathSpec.from_lines(
            "gitignore", self.config.read_rules.include
        )
        exclude_spec = pathspec.PathSpec.from_lines(
            "gitignore", self.config.read_rules.exclude
        )
        return include_spec.match_file(rel_path) and not exclude_spec.match_file(
            rel_path
        )

    def _is_append_allowed(self, rel_path: str) -> bool:
        """Check if a file matches append_allowed patterns."""
        append_spec = pathspec.PathSpec.from_lines(
            "gitignore", self.config.read_rules.append_allowed
        )
        return append_spec.match_file(rel_path)

    def execute(
        self, tool_name: str, tool_input: dict[str, Any], user_id: int = 0
    ) -> ToolResult:
        """Execute a tool synchronously (legacy, prefer execute_async)."""
        return self.execute_direct(tool_name, tool_input, user_id=user_id)

    def execute_direct(
        self, tool_name: str, tool_input: dict[str, Any], user_id: int = 0
    ) -> ToolResult:
        """Execute a tool directly without going through the scheduler.

        This is the core execution method used by the scheduler for all tools.
        """
        start_time = time.time()

        handlers = {
            "list_files": self._list_files,
            "read_file": self._read_file,
            "read_files": self._read_files,
            "search_files": self._search_files,
            "write_file": self._write_file,
            "read_activity_log": self._read_activity_log,
            "enable_file_notifications": lambda ti: self._enable_file_notifications(
                ti, user_id
            ),
            "disable_file_notifications": lambda ti: self._disable_file_notifications(
                ti, user_id
            ),
            "get_file_notification_status": (
                lambda ti: self._get_file_notification_status(ti, user_id)
            ),
        }

        handler = handlers.get(tool_name)
        if handler:
            try:
                result = handler(tool_input)
                self._log_tool_call(tool_name, tool_input, result, start_time, user_id)
                return result
            except Exception as e:
                result = ToolResult(content=f"Tool execution error: {e}", is_error=True)
                self._log_tool_call(tool_name, tool_input, result, start_time, user_id)
                return result

        # Try utility tools
        try:
            util_result = self._util_tools.execute(tool_name, tool_input)
            if util_result is not None:
                self._log_tool_call(
                    tool_name, tool_input, util_result, start_time, user_id
                )
                return util_result
        except Exception as e:
            error_result = ToolResult(content=f"Utility tool error: {e}", is_error=True)
            self._log_tool_call(
                tool_name, tool_input, error_result, start_time, user_id
            )
            return error_result

        # Try web tools
        try:
            web_result = self._web_tools.execute(tool_name, tool_input)
            if web_result is not None:
                self._log_tool_call(
                    tool_name, tool_input, web_result, start_time, user_id
                )
                return web_result
        except Exception as e:
            error_result = ToolResult(content=f"Web tool error: {e}", is_error=True)
            self._log_tool_call(
                tool_name, tool_input, error_result, start_time, user_id
            )
            return error_result

        # Try custom tools if available
        if self._custom_tools:
            try:
                custom_result = self._custom_tools.execute(tool_name, tool_input)
                self._log_tool_call(
                    tool_name, tool_input, custom_result, start_time, user_id
                )
                return custom_result
            except Exception as e:
                error_result = ToolResult(
                    content=f"Custom tool execution error: {e}", is_error=True
                )
                self._log_tool_call(
                    tool_name, tool_input, error_result, start_time, user_id
                )
                return error_result

        return ToolResult(content=f"Unknown tool: {tool_name}", is_error=True)

    def _log_tool_call(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        result: ToolResult,
        start_time: float,
        user_id: int,
    ) -> None:
        """Log a tool call to the activity log."""
        duration_ms = int((time.time() - start_time) * 1000)
        self._activity_logger.log_tool_call(
            tool_name=tool_name,
            tool_input=tool_input,
            result=result.content,
            is_error=result.is_error,
            user_id=user_id,
            duration_ms=duration_ms,
        )

    async def execute_async(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        chat_id: int = 0,
        user_id: int = 0,
    ) -> ToolResult:
        """Execute a tool through the unified scheduler path.

        All tool calls go through the scheduler for consistent logging,
        monitoring, and potential safeguards.
        """
        # Try scheduler tools first (these are special: schedule_task, list_tasks, etc.)
        if self._scheduler_tools:
            try:
                result = await self._scheduler_tools.execute(
                    tool_name, tool_input, chat_id, user_id
                )
                if result is not None:
                    # Scheduler tools handle their own logging
                    return result
            except Exception as e:
                return ToolResult(content=f"Scheduler tool error: {e}", is_error=True)

        # Route all other tools through scheduler.execute_immediate
        if self._scheduler is not None:
            return await self._scheduler.execute_immediate(
                tool_name, tool_input, user_id=user_id
            )

        # Fallback if scheduler not set (e.g., during tests)
        return self.execute_direct(tool_name, tool_input, user_id=user_id)

    def _list_files(self, tool_input: dict[str, Any]) -> ToolResult:
        """List files in a directory."""
        params = ListFilesInput(**tool_input)

        target_dir = self._validate_path(params.path)
        if target_dir is None:
            return ToolResult(content="Invalid path: access denied", is_error=True)

        if not target_dir.exists():
            return ToolResult(
                content=f"Directory not found: {params.path}", is_error=True
            )

        if not target_dir.is_dir():
            return ToolResult(content=f"Not a directory: {params.path}", is_error=True)

        files: list[str] = []
        for file_path in target_dir.rglob(params.pattern):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(self._root))
                if self._is_file_allowed(rel_path):
                    files.append(rel_path)

        files.sort()

        if not files:
            return ToolResult(content="No matching files found.")

        # Limit output to prevent token overflow
        total_count = len(files)
        if total_count > self.MAX_LIST_FILES:
            files = files[: self.MAX_LIST_FILES]
            return ToolResult(
                content="\n".join(files)
                + f"\n\n[Showing first {self.MAX_LIST_FILES} of {total_count} files]"
            )

        return ToolResult(content="\n".join(files))

    def _read_file(self, tool_input: dict[str, Any]) -> ToolResult:
        """Read a file's contents."""
        params = ReadFileInput(**tool_input)

        file_path = self._validate_path(params.path)
        if file_path is None:
            return ToolResult(content="Invalid path: access denied", is_error=True)

        if not file_path.exists():
            return ToolResult(content=f"File not found: {params.path}", is_error=True)

        if not file_path.is_file():
            return ToolResult(content=f"Not a file: {params.path}", is_error=True)

        rel_path = str(file_path.relative_to(self._root))
        if not self._is_file_allowed(rel_path):
            return ToolResult(
                content=f"File not accessible: {params.path}", is_error=True
            )

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            # Truncate very large files
            if len(content) > self.MAX_FILE_READ_CHARS:
                content = (
                    content[: self.MAX_FILE_READ_CHARS]
                    + f"\n\n[Truncated at {self.MAX_FILE_READ_CHARS} characters]"
                )
            return ToolResult(content=content)
        except Exception as e:
            return ToolResult(content=f"Error reading file: {e}", is_error=True)

    def _read_files(self, tool_input: dict[str, Any]) -> ToolResult:
        """Read multiple files and concatenate their contents."""
        params = ReadFilesInput(**tool_input)

        if not params.paths:
            return ToolResult(
                content="paths is required and cannot be empty", is_error=True
            )

        parts: list[str] = []
        errors: list[str] = []
        total_chars = 0

        for path in params.paths:
            file_path = self._validate_path(path)
            if file_path is None:
                errors.append(f"{path}: access denied")
                continue

            if not file_path.exists():
                errors.append(f"{path}: not found")
                continue

            if not file_path.is_file():
                errors.append(f"{path}: not a file")
                continue

            rel_path = str(file_path.relative_to(self._root))
            if not self._is_file_allowed(rel_path):
                errors.append(f"{path}: not accessible")
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")

                # Check if adding this would exceed limit
                file_block = f"## {rel_path}\n\n{content}\n\n"
                if total_chars + len(file_block) > self.MAX_FILE_READ_CHARS:
                    parts.append(
                        f"[Truncated - limit of {self.MAX_FILE_READ_CHARS} chars reached]"
                    )
                    break

                parts.append(file_block)
                total_chars += len(file_block)
            except Exception as e:
                errors.append(f"{path}: {e}")

        result_parts: list[str] = []
        if parts:
            result_parts.append("".join(parts))
        if errors:
            result_parts.append("Errors:\n" + "\n".join(f"  - {e}" for e in errors))

        if not parts:
            # No files were successfully read
            if errors:
                return ToolResult(
                    content="No files could be read:\n"
                    + "\n".join(f"  - {e}" for e in errors),
                    is_error=True,
                )
            return ToolResult(content="No files could be read", is_error=True)

        return ToolResult(content="\n".join(result_parts))

    def _search_files(self, tool_input: dict[str, Any]) -> ToolResult:
        """Search for text across files."""
        params = SearchFilesInput(**tool_input)

        pattern = re.compile(re.escape(params.query), re.IGNORECASE)
        results: list[str] = []

        for file_path in self._root.rglob("*"):
            if not file_path.is_file():
                continue

            rel_path = str(file_path.relative_to(self._root))
            if not self._is_file_allowed(rel_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                matches = list(pattern.finditer(content))
                if matches:
                    # Extract context around first match
                    match = matches[0]
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 50)
                    excerpt = content[start:end].replace("\n", " ")
                    results.append(f"{rel_path}:\n  ...{excerpt}...")

                    if len(results) >= params.max_results:
                        break
            except Exception:
                continue

        if not results:
            return ToolResult(content=f"No files contain '{params.query}'")

        return ToolResult(content="\n\n".join(results))

    def _write_file(self, tool_input: dict[str, Any]) -> ToolResult:
        """Write content to a file."""
        params = WriteFileInput(**tool_input)

        file_path = self._validate_path(params.path)
        if file_path is None:
            return ToolResult(content="Invalid path: access denied", is_error=True)

        rel_path = str(file_path.relative_to(self._root))
        if not self._is_file_allowed(rel_path):
            return ToolResult(
                content=f"Cannot write to '{params.path}': does not match allowed file patterns",
                is_error=True,
            )

        # Check append permissions
        if params.mode == WriteMode.append and not self._is_append_allowed(rel_path):
            return ToolResult(
                content=f"Cannot append to '{params.path}': not in append_allowed patterns",
                is_error=True,
            )

        try:
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_existed = file_path.exists()
            content = params.content
            if params.mode == WriteMode.append and file_existed:
                existing = file_path.read_text(encoding="utf-8", errors="replace")
                content = existing + content

            file_path.write_text(content, encoding="utf-8")

            if params.mode == WriteMode.append:
                action = "Appended to" if file_existed else "Created"
            else:
                action = "Updated" if file_existed else "Created"
            return ToolResult(content=f"{action} {rel_path}")
        except Exception as e:
            return ToolResult(content=f"Error writing file: {e}", is_error=True)

    def _read_activity_log(self, tool_input: dict[str, Any]) -> ToolResult:
        """Read the activity log."""
        params = ReadActivityLogInput(**tool_input)
        try:
            content = self._activity_logger.read_log(
                last_n=params.last_n,
                tool_filter=params.tool_filter,
                date=params.date,
                search=params.search,
            )
            return ToolResult(content=content)
        except Exception as e:
            return ToolResult(content=f"Error reading activity log: {e}", is_error=True)

    def _enable_file_notifications(
        self, tool_input: dict[str, Any], user_id: int
    ) -> ToolResult:
        """Enable file change notifications for a user."""
        if not self._session_manager:
            return ToolResult(content="Session manager not available", is_error=True)
        if not user_id:
            return ToolResult(content="User ID not available", is_error=True)

        self._session_manager.set_file_notifications_enabled(user_id, True)
        return ToolResult(
            content="File change notifications enabled. You will now receive "
            "notifications when files are created, modified, or deleted."
        )

    def _disable_file_notifications(
        self, tool_input: dict[str, Any], user_id: int
    ) -> ToolResult:
        """Disable file change notifications for a user."""
        if not self._session_manager:
            return ToolResult(content="Session manager not available", is_error=True)
        if not user_id:
            return ToolResult(content="User ID not available", is_error=True)

        self._session_manager.set_file_notifications_enabled(user_id, False)
        return ToolResult(content="File change notifications disabled.")

    def _get_file_notification_status(
        self, tool_input: dict[str, Any], user_id: int
    ) -> ToolResult:
        """Get file notification status for a user."""
        if not self._session_manager:
            return ToolResult(content="Session manager not available", is_error=True)
        if not user_id:
            return ToolResult(content="User ID not available", is_error=True)

        enabled = self._session_manager.get_file_notifications_enabled(user_id)
        status = "enabled" if enabled else "disabled"
        return ToolResult(content=f"File change notifications are {status}.")

    @property
    def activity_logger(self) -> ActivityLogger:
        """Expose activity logger for external use (e.g., message logging)."""
        return self._activity_logger

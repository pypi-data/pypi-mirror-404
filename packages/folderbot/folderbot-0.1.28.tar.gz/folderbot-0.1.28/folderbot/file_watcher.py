"""File change watcher with Telegram notifications."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

if TYPE_CHECKING:
    from .config import WatchConfig

logger = logging.getLogger(__name__)


class FileChangeHandler(FileSystemEventHandler):
    """Handles file system events and queues notifications."""

    def __init__(
        self,
        root_folder: Path,
        config: WatchConfig,
        notify_callback: Callable[[str], Coroutine[None, None, None]],
        loop: asyncio.AbstractEventLoop,
    ):
        self.root_folder = root_folder
        self.config = config
        self.notify_callback = notify_callback
        self.loop = loop
        self._pending_events: dict[str, str] = {}  # path -> event_type
        self._debounce_task: asyncio.Task | None = None

    def _matches_patterns(self, path: Path, patterns: list[str]) -> bool:
        """Check if path matches any of the glob patterns."""
        try:
            rel_path = path.relative_to(self.root_folder)
        except ValueError:
            return False

        from pathspec import PathSpec

        spec = PathSpec.from_lines("gitwildmatch", patterns)
        return spec.match_file(str(rel_path))

    def _should_notify(self, path: Path) -> bool:
        """Check if we should notify about this path."""
        # Must match include patterns
        if not self._matches_patterns(path, self.config.include):
            return False

        # Must not match exclude patterns
        if self._matches_patterns(path, self.config.exclude):
            return False

        return True

    def _queue_event(self, event_type: str, src_path: str) -> None:
        """Queue an event for debounced notification."""
        path = Path(src_path)

        if not self._should_notify(path):
            return

        self._pending_events[src_path] = event_type

        # Schedule debounced notification
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()

        self._debounce_task = asyncio.run_coroutine_threadsafe(
            self._send_debounced_notification(), self.loop
        ).result()

    async def _send_debounced_notification(self) -> None:
        """Wait for debounce period then send notification."""
        await asyncio.sleep(self.config.debounce_seconds)

        if not self._pending_events:
            return

        # Build notification message
        events = self._pending_events.copy()
        self._pending_events.clear()

        lines = ["📁 File changes detected:"]
        for path, event_type in sorted(events.items()):
            try:
                rel_path = Path(path).relative_to(self.root_folder)
            except ValueError:
                rel_path = Path(path)

            emoji = {"created": "➕", "modified": "✏️", "deleted": "🗑️"}.get(
                event_type, "📄"
            )
            lines.append(f"  {emoji} {event_type}: {rel_path}")

        message = "\n".join(lines)
        logger.info(f"Sending file change notification: {len(events)} changes")

        try:
            await self.notify_callback(message)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            src_path = (
                event.src_path
                if isinstance(event.src_path, str)
                else event.src_path.decode()
            )
            self._queue_event("created", src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            src_path = (
                event.src_path
                if isinstance(event.src_path, str)
                else event.src_path.decode()
            )
            self._queue_event("modified", src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            src_path = (
                event.src_path
                if isinstance(event.src_path, str)
                else event.src_path.decode()
            )
            self._queue_event("deleted", src_path)


class FileWatcher:
    """Watches a folder for changes and sends Telegram notifications."""

    def __init__(
        self,
        root_folder: Path,
        config: WatchConfig,
        notify_callback: Callable[[str], Coroutine[None, None, None]],
    ):
        self.root_folder = root_folder
        self.config = config
        self.notify_callback = notify_callback
        self._observer: Any = None
        self._handler: FileChangeHandler | None = None

    async def start(self) -> None:
        """Start watching for file changes."""
        loop = asyncio.get_event_loop()

        self._handler = FileChangeHandler(
            self.root_folder, self.config, self.notify_callback, loop
        )

        self._observer = Observer()
        self._observer.schedule(self._handler, str(self.root_folder), recursive=True)
        self._observer.start()

        logger.info(f"File watcher started for {self.root_folder}")

    async def stop(self) -> None:
        """Stop watching for file changes."""
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
            logger.info("File watcher stopped")

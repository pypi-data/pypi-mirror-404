"""Telegram bot handler."""

import asyncio
import logging
import re
from datetime import datetime
from typing import Any

from anthropic import APIStatusError
from telegram import Bot, Message, Update
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from . import __version__
from .claude_client import ClaudeClient
from .config import Config
from .context_builder import ContextBuilder
from .file_watcher import FileWatcher
from .migration import migrate_database
from .scheduler import SchedulerTools, TaskScheduler, TaskStore
from .session_manager import SessionManager

logger = logging.getLogger(__name__)


def _markdown_to_html(text: str) -> str:
    """Convert common Markdown formatting to Telegram HTML.

    Handles:
    - **bold** or __bold__ → <b>bold</b>
    - *italic* or _italic_ → <i>italic</i>
    - `code` → <code>code</code>
    - ```code block``` → <pre>code block</pre>
    """
    # Code blocks first (``` ... ```) - must come before inline code
    text = re.sub(r"```(\w*)\n?(.*?)```", r"<pre>\2</pre>", text, flags=re.DOTALL)

    # Inline code (` ... `)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

    # Bold: **text** or __text__ (must come before italic)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)

    # Italic: *text* or _text_ (but not inside words like file_name)
    # Only match * for italic to avoid false positives with underscores in names
    text = re.sub(r"(?<!\w)\*([^*]+)\*(?!\w)", r"<i>\1</i>", text)

    return text


class TelegramBot:
    """Main Telegram bot class."""

    def __init__(self, config: Config):
        self.config = config
        self.context_builder = ContextBuilder(config)

        # Migrate data from old global database if needed
        migrate_database(config.db_path, config.allowed_user_ids)

        self.session_manager = SessionManager(config.db_path)

        # Initialize scheduler
        self._task_store = TaskStore(config.db_path)
        self._scheduler = TaskScheduler(
            task_store=self._task_store,
            send_message=self._send_scheduler_message,
            summarize=self._summarize_for_scheduler,
        )
        self._scheduler_tools = SchedulerTools(self._scheduler)

        # Create Claude client with scheduler tools
        self.claude_client = ClaudeClient(config, scheduler_tools=self._scheduler_tools)

        # Wire up the circular dependencies:
        # - Scheduler needs folder_tools to execute tools
        # - FolderTools needs scheduler for unified execution path
        # - FolderTools needs session_manager for file notification preferences
        self._scheduler.set_folder_tools(self.claude_client.tools)
        self.claude_client.tools.set_scheduler(self._scheduler)
        self.claude_client.tools.set_session_manager(self.session_manager)

        # Initialize file watcher (sends notifications on file changes)
        self._file_watcher = FileWatcher(
            config.root_folder,
            config.watch_config,
            self._send_file_change_notification,
        )

        # Application reference (set in run())
        self._application: Application | None = None  # type: ignore[type-arg]

        # Track pending messages per user (accumulated while processing)
        self._pending_messages: dict[int, list[str]] = {}
        # Track current processing task per user (for cancellation)
        self._processing_tasks: dict[int, asyncio.Task] = {}
        # Track the latest update object for sending responses
        self._pending_updates: dict[int, Update] = {}
        # Track cancelled state per user (to prevent responses after cancellation)
        self._cancelled_users: set[int] = set()
        # Track messages currently being processed (to restore on cancellation)
        self._processing_messages: dict[int, list[str]] = {}

    def _is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized."""
        return user_id in self.config.allowed_user_ids

    @staticmethod
    async def _reply_text(message: Message, text: str, **kwargs: Any) -> None:
        """Reply with HTML parse_mode, falling back to plain text on failure."""
        text = _markdown_to_html(text)
        try:
            await message.reply_text(text, parse_mode="HTML", **kwargs)
        except BadRequest:
            await message.reply_text(text, **kwargs)

    @staticmethod
    async def _send_text(bot: Bot, chat_id: int, text: str, **kwargs: Any) -> None:
        """Send message with HTML parse_mode, falling back to plain text on failure."""
        text = _markdown_to_html(text)
        try:
            await bot.send_message(
                chat_id=chat_id, text=text, parse_mode="HTML", **kwargs
            )
        except BadRequest:
            await bot.send_message(chat_id=chat_id, text=text, **kwargs)

    def _log_conversation(self, user_message: str, assistant_message: str) -> None:
        """Log conversation to daily log file."""
        log_folder = self.config.root_folder / self.config.auto_log_folder
        log_folder.mkdir(parents=True, exist_ok=True)

        today = datetime.now().strftime("%Y-%m-%d")
        log_file = log_folder / f"{today}.md"

        timestamp = datetime.now().strftime("%H:%M")
        entry = f"\n### {timestamp}\n\n**{self.config.user_name}:** {user_message}\n\n**Claude:** {assistant_message}\n"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)

    async def _check_version_notification(self, user_id: int, update: Update) -> None:
        """Check if user needs to be notified about a new version."""
        if not update.message:
            return

        last_version = self.session_manager.get_last_notified_version(user_id)

        if last_version != __version__:
            logger.info(
                f"[{user_id}] New version notification: {last_version} -> {__version__}"
            )
            await self._reply_text(
                update.message, f"Folderbot updated to v{__version__}"
            )
            self.session_manager.set_last_notified_version(user_id, __version__)

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command."""
        if not update.effective_user or not update.message:
            return

        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            await self._reply_text(update.message, "Unauthorized.")
            return

        await self._reply_text(
            update.message,
            "Self-bot ready. Send me a message to chat with your folder.\n\n"
            "Commands:\n"
            "/clear - Clear conversation history\n"
            "/new - Start new topic\n"
            "/status - Show session info\n"
            "/files - List files in context\n"
            "/tasks - List scheduled tasks",
        )

    async def clear_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /clear command."""
        if not update.effective_user or not update.message:
            return

        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            await self._reply_text(update.message, "Unauthorized.")
            return

        self.session_manager.clear_session(user_id)
        await self._reply_text(update.message, "Conversation history cleared.")

    async def new_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /new command."""
        if not update.effective_user or not update.message:
            return

        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            await self._reply_text(update.message, "Unauthorized.")
            return

        # Clear session and signal new topic
        self.session_manager.clear_session(user_id)
        await self._reply_text(update.message, "New topic started. History cleared.")

    async def status_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /status command."""
        if not update.effective_user or not update.message:
            return

        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            await self._reply_text(update.message, "Unauthorized.")
            return

        session_info = self.session_manager.get_session_info(user_id)
        context_stats = self.context_builder.get_context_stats()

        status = (
            f"Session:\n"
            f"  Messages: {session_info['message_count']}\n"
            f"  Last update: {session_info['updated_at'] or 'Never'}\n\n"
            f"Context:\n"
            f"  Files: {context_stats['file_count']}\n"
            f"  Size: {context_stats['total_chars']:,} chars\n"
            f"  Cache age: {context_stats['cache_age_seconds']}s"
        )
        await self._reply_text(update.message, status)

    async def files_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /files command."""
        if not update.effective_user or not update.message:
            return

        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            await self._reply_text(update.message, "Unauthorized.")
            return

        files = self.context_builder.get_file_list()

        if not files:
            await self._reply_text(update.message, "No files in context.")
            return

        # Truncate if too many files
        if len(files) > 50:
            file_list = "\n".join(files[:50])
            file_list += f"\n... and {len(files) - 50} more"
        else:
            file_list = "\n".join(files)

        await self._reply_text(
            update.message, f"Files in context ({len(files)}):\n\n{file_list}"
        )

    async def handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle regular messages with immediate processing and restart on new message."""
        if not update.effective_user or not update.message or not update.message.text:
            return

        user_id = update.effective_user.id
        user_message = update.message.text

        logger.info(f"[{user_id}] Message received: {user_message[:50]}...")

        if not self._is_authorized(user_id):
            await self._reply_text(update.message, "Unauthorized.")
            return

        # Check for version update notification (only on first message)
        await self._check_version_notification(user_id, update)

        # Add message to pending list
        if user_id not in self._pending_messages:
            self._pending_messages[user_id] = []
        self._pending_messages[user_id].append(user_message)
        self._pending_updates[user_id] = update
        logger.info(
            f"[{user_id}] Added to pending. Total pending: {len(self._pending_messages[user_id])}"
        )

        # Check if already processing for this user
        if user_id in self._processing_tasks:
            task = self._processing_tasks[user_id]
            if not task.done():
                # Already processing - cancel it, messages are accumulated
                logger.info(f"[{user_id}] Existing task found, cancelling...")
                self._cancelled_users.add(user_id)
                task.cancel()
                # Wait for cancellation to complete before starting new task
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                logger.info(f"[{user_id}] Previous task cancelled successfully")

                # Restore messages that were being processed
                if user_id in self._processing_messages:
                    cancelled_msgs = self._processing_messages.pop(user_id)
                    logger.info(
                        f"[{user_id}] Restoring {len(cancelled_msgs)} cancelled message(s)"
                    )
                    # Prepend to pending so they come first
                    if user_id in self._pending_messages:
                        self._pending_messages[user_id] = (
                            cancelled_msgs + self._pending_messages[user_id]
                        )
                    else:
                        self._pending_messages[user_id] = cancelled_msgs
            else:
                logger.info(f"[{user_id}] Existing task already done")

        # Clear cancelled state before starting new processing
        self._cancelled_users.discard(user_id)

        # Start processing with all accumulated messages
        await self._start_processing(user_id)

    async def _start_processing(self, user_id: int) -> None:
        """Start processing accumulated messages for a user."""
        # Collect all pending messages
        messages = self._pending_messages.pop(user_id, [])
        update = self._pending_updates.pop(user_id, None)

        if not messages or not update or not update.message:
            logger.info(f"[{user_id}] _start_processing: no messages to process")
            return

        # Track messages being processed (for restoration if cancelled)
        self._processing_messages[user_id] = messages

        # Combine multiple messages into one
        combined_message = "\n".join(messages)
        logger.info(f"[{user_id}] Starting processing with {len(messages)} message(s)")

        # Start processing task (can be cancelled if new message arrives)
        task = asyncio.create_task(
            self._process_message(user_id, combined_message, update)
        )
        self._processing_tasks[user_id] = task
        logger.info(f"[{user_id}] Processing task created")

    async def _process_message(
        self, user_id: int, user_message: str, update: Update
    ) -> None:
        """Process a message and send response."""
        if not update.message:
            return

        logger.info(f"[{user_id}] _process_message started")

        # Show typing indicator (native Telegram indicator, no custom message)
        await update.message.chat.send_action("typing")

        try:
            # Check if cancelled before making API call
            if user_id in self._cancelled_users:
                logger.info(f"[{user_id}] Cancelled before API call, aborting")
                return

            # Get conversation history
            history = self.session_manager.get_history(user_id)

            # Tools handle file access now - context is no longer pre-loaded
            folder_context = ""

            logger.info(f"[{user_id}] Calling Claude API...")

            # Get response from Claude (with tool use)
            response, tools_used = await self.claude_client.chat(
                user_message,
                folder_context,
                history,
                chat_id=update.message.chat_id,
                user_id=user_id,
            )

            # Append tools used (deterministic, no LLM involved)
            if tools_used:
                # Deduplicate while preserving order
                seen: set[str] = set()
                unique_tools: list[str] = []
                for t in tools_used:
                    if t not in seen:
                        seen.add(t)
                        unique_tools.append(t)
                response += f"\n\n<i>Tools: {', '.join(unique_tools)}</i>"

            # Log to activity log (deterministic)
            self.claude_client.tools.activity_logger.log_message(
                direction="user",
                content=user_message,
                user_id=user_id,
            )
            self.claude_client.tools.activity_logger.log_message(
                direction="assistant",
                content=response,
                user_id=user_id,
                tools_used=tools_used if tools_used else None,
            )

            logger.info(
                f"[{user_id}] Claude API returned, response length: {len(response)}"
            )

            # Check if we were cancelled (either via task or flag)
            if asyncio.current_task() and asyncio.current_task().cancelled():  # type: ignore[union-attr]
                logger.info(f"[{user_id}] Task cancelled after API call, aborting")
                return

            if user_id in self._cancelled_users:
                logger.info(f"[{user_id}] Cancelled flag set after API call, aborting")
                return

            # Store messages in session
            self.session_manager.add_message(user_id, "user", user_message)
            self.session_manager.add_message(user_id, "assistant", response)

            # Log to file
            self._log_conversation(user_message, response)

            # Final cancellation check before sending
            if user_id in self._cancelled_users:
                logger.info(f"[{user_id}] Cancelled before send, aborting")
                return

            logger.info(f"[{user_id}] Sending response to Telegram...")

            # Send response (split if too long)
            if len(response) > 4096:
                # Telegram message limit
                for i in range(0, len(response), 4096):
                    if user_id in self._cancelled_users:
                        logger.info(
                            f"[{user_id}] Cancelled during split send, aborting"
                        )
                        return
                    await self._reply_text(update.message, response[i : i + 4096])
            else:
                await self._reply_text(update.message, response)

            logger.info(f"[{user_id}] Response sent successfully")

            # Clear processing messages on success
            self._processing_messages.pop(user_id, None)

        except asyncio.CancelledError:
            logger.info(f"[{user_id}] CancelledError caught, response cancelled")
            # Don't send anything - user sent a new message
        except APIStatusError as e:
            logger.exception("Anthropic API error")
            status_code = e.response.status_code if e.response else 0
            if status_code == 429:
                await self._reply_text(
                    update.message,
                    "Claude is busy at the moment. Please try again in a few seconds.",
                )
            elif status_code >= 500:
                await self._reply_text(
                    update.message,
                    "Claude is temporarily unavailable. Please try again in a moment.",
                )
            else:
                await self._reply_text(
                    update.message,
                    "There was a problem connecting to Claude. Please try again.",
                )
        except Exception as e:
            logger.exception("Error handling message")
            await self._reply_text(update.message, f"Error: {e}")

    async def wait_for_processing(self, user_id: int) -> None:
        """Wait for any pending processing to complete. For testing."""
        if user_id in self._processing_tasks:
            task = self._processing_tasks[user_id]
            if not task.done():
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def _send_scheduler_message(self, chat_id: int, text: str) -> None:
        """Send a message from the scheduler to a Telegram chat."""
        if not self._application:
            logger.warning("Cannot send scheduler message: application not set")
            return
        bot = self._application.bot
        if len(text) > 4096:
            for i in range(0, len(text), 4096):
                await self._send_text(bot, chat_id, text[i : i + 4096])
        else:
            await self._send_text(bot, chat_id, text)

    async def _summarize_for_scheduler(self, prompt: str, chat_id: int) -> str:
        """Call Claude to summarize task results."""
        response, _ = await self.claude_client.chat(
            user_message=prompt,
            context="",
            history=[],
        )
        return response

    async def _send_file_change_notification(self, message: str) -> None:
        """Send file change notification to users who have enabled them."""
        if not self._application:
            logger.warning("Cannot send file notification: application not set")
            return

        # Only notify users who have enabled file notifications
        enabled_users = self.session_manager.get_users_with_file_notifications()
        # Filter to allowed users only (in case DB has stale data)
        users_to_notify = [
            uid for uid in enabled_users if uid in self.config.allowed_user_ids
        ]

        if not users_to_notify:
            return

        bot = self._application.bot
        for user_id in users_to_notify:
            try:
                await self._send_text(bot, user_id, message)
            except Exception as e:
                logger.warning(f"[{user_id}] Could not send file notification: {e}")

    async def tasks_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /tasks command."""
        if not update.effective_user or not update.message:
            return

        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            await self._reply_text(update.message, "Unauthorized.")
            return

        tasks = self._scheduler.list_tasks(user_id)
        if not tasks:
            await self._reply_text(update.message, "No scheduled tasks.")
            return

        lines = []
        for t in tasks[:20]:
            lines.append(f"  {t.task_id}  [{t.status.value}]  {t.description}")
        await self._reply_text(update.message, "Scheduled tasks:\n" + "\n".join(lines))

    async def _post_init(self, application: Application) -> None:  # type: ignore[type-arg]
        """Called after application is initialized."""
        await self._scheduler.start()
        logger.info("Task scheduler started")

        await self._file_watcher.start()

        # Send startup message to all allowed users
        await self._send_startup_messages()

    async def _send_startup_messages(self) -> None:
        """Send startup message to all allowed users with version update if applicable."""
        if not self._application:
            return

        bot = self._application.bot

        for user_id in self.config.allowed_user_ids:
            try:
                # Check for version update
                last_version = self.session_manager.get_last_notified_version(user_id)

                if last_version and last_version != __version__:
                    # Version changed - notify about update
                    message = f"Hi! Folderbot is back online.\n\nUpdated: v{last_version} → v{__version__}"
                    self.session_manager.set_last_notified_version(user_id, __version__)
                    logger.info(f"[{user_id}] Startup with version update notification")
                elif last_version:
                    # Same version - just say hi
                    message = f"Hi! Folderbot is back online. (v{__version__})"
                    logger.info(f"[{user_id}] Startup message sent")
                else:
                    # First time user - set version, skip message
                    # (they haven't used the bot yet, so don't spam them)
                    self.session_manager.set_last_notified_version(user_id, __version__)
                    logger.info(
                        f"[{user_id}] First time user, version set, no startup message"
                    )
                    continue

                # Send to user (user_id == chat_id for private chats)
                await self._send_text(
                    bot,
                    user_id,
                    message,
                    connect_timeout=10,
                    read_timeout=10,
                )

            except Exception as e:
                # User may have blocked bot or never started it
                logger.warning(f"[{user_id}] Could not send startup message: {e}")

    async def _post_shutdown(self, application: Application) -> None:  # type: ignore[type-arg]
        """Called during application shutdown."""
        await self._file_watcher.stop()
        await self._scheduler.shutdown()
        logger.info("Task scheduler stopped")

    def run(self) -> None:
        """Run the bot."""
        application = Application.builder().token(self.config.telegram_token).build()
        self._application = application

        # Scheduler lifecycle hooks
        application.post_init = self._post_init
        application.post_shutdown = self._post_shutdown

        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("clear", self.clear_command))
        application.add_handler(CommandHandler("new", self.new_command))
        application.add_handler(CommandHandler("status", self.status_command))
        application.add_handler(CommandHandler("files", self.files_command))
        application.add_handler(CommandHandler("tasks", self.tasks_command))
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        # Run the bot
        logger.info("Starting bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

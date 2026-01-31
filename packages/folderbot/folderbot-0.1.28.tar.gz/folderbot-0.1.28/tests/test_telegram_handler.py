"""Tests for Telegram bot handler."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, call, patch

import httpx
import pytest
from anthropic import APIStatusError

from folderbot.config import Config, ReadRules, WatchConfig
from folderbot.telegram_handler import TelegramBot


@pytest.fixture
def mock_config(tmp_path: Path) -> Config:
    """Create a mock config for testing."""
    config = MagicMock(spec=Config)
    config.telegram_token = "test_token"
    config.anthropic_api_key = "test_api_key"
    config.root_folder = tmp_path
    config.allowed_user_ids = [12345, 67890]
    config.read_rules = ReadRules()
    config.watch_config = WatchConfig()
    config.auto_log_folder = "logs/"
    config.db_path = tmp_path / "sessions.db"
    config.model = "claude-sonnet-4-20250514"
    config.max_context_chars = 10000
    return config


@pytest.fixture
def bot(mock_config: Config) -> TelegramBot:
    """Create a bot instance for testing."""
    return TelegramBot(mock_config)


@pytest.fixture
def mock_update():
    """Create a mock Telegram update."""
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 12345
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.message.chat = MagicMock()
    update.message.chat.send_action = AsyncMock()
    return update


class TestAuthorization:
    def test_authorized_user(self, bot: TelegramBot):
        assert bot._is_authorized(12345) is True
        assert bot._is_authorized(67890) is True

    def test_unauthorized_user(self, bot: TelegramBot):
        assert bot._is_authorized(99999) is False
        assert bot._is_authorized(0) is False


class TestStartCommand:
    @pytest.mark.asyncio
    async def test_start_authorized(self, bot: TelegramBot, mock_update):
        await bot.start_command(mock_update, MagicMock())

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Self-bot ready" in call_args
        assert "/clear" in call_args

    @pytest.mark.asyncio
    async def test_start_unauthorized(self, bot: TelegramBot, mock_update):
        mock_update.effective_user.id = 99999

        await bot.start_command(mock_update, MagicMock())

        mock_update.message.reply_text.assert_called_once_with(
            "Unauthorized.", parse_mode="HTML"
        )

    @pytest.mark.asyncio
    async def test_start_no_user(self, bot: TelegramBot, mock_update):
        mock_update.effective_user = None

        await bot.start_command(mock_update, MagicMock())

        mock_update.message.reply_text.assert_not_called()


class TestClearCommand:
    @pytest.mark.asyncio
    async def test_clear_authorized(self, bot: TelegramBot, mock_update):
        # Add some messages first
        bot.session_manager.add_message(12345, "user", "test")

        await bot.clear_command(mock_update, MagicMock())

        mock_update.message.reply_text.assert_called_once_with(
            "Conversation history cleared.", parse_mode="HTML"
        )
        assert bot.session_manager.get_history(12345) == []

    @pytest.mark.asyncio
    async def test_clear_unauthorized(self, bot: TelegramBot, mock_update):
        mock_update.effective_user.id = 99999

        await bot.clear_command(mock_update, MagicMock())

        mock_update.message.reply_text.assert_called_once_with(
            "Unauthorized.", parse_mode="HTML"
        )


class TestNewCommand:
    @pytest.mark.asyncio
    async def test_new_authorized(self, bot: TelegramBot, mock_update):
        bot.session_manager.add_message(12345, "user", "old message")

        await bot.new_command(mock_update, MagicMock())

        mock_update.message.reply_text.assert_called_once_with(
            "New topic started. History cleared.", parse_mode="HTML"
        )
        assert bot.session_manager.get_history(12345) == []


class TestStatusCommand:
    @pytest.mark.asyncio
    async def test_status_authorized(self, bot: TelegramBot, mock_update):
        bot.session_manager.add_message(12345, "user", "test message")

        await bot.status_command(mock_update, MagicMock())

        mock_update.message.reply_text.assert_called_once()
        status_text = mock_update.message.reply_text.call_args[0][0]
        assert "Messages: 1" in status_text
        assert "Files:" in status_text

    @pytest.mark.asyncio
    async def test_status_unauthorized(self, bot: TelegramBot, mock_update):
        mock_update.effective_user.id = 99999

        await bot.status_command(mock_update, MagicMock())

        mock_update.message.reply_text.assert_called_once_with(
            "Unauthorized.", parse_mode="HTML"
        )


class TestFilesCommand:
    @pytest.mark.asyncio
    async def test_files_empty(self, bot: TelegramBot, mock_update):
        await bot.files_command(mock_update, MagicMock())

        mock_update.message.reply_text.assert_called_once_with(
            "No files in context.", parse_mode="HTML"
        )

    @pytest.mark.asyncio
    async def test_files_with_content(
        self, bot: TelegramBot, mock_update, mock_config: Config
    ):
        # Create a test file
        (mock_config.root_folder / "test.md").write_text("# Test")

        # Force cache refresh
        bot.context_builder._cache_time = 0

        await bot.files_command(mock_update, MagicMock())

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "test.md" in call_args


class TestHandleMessage:
    @pytest.mark.asyncio
    async def test_unauthorized_message(self, bot: TelegramBot, mock_update):
        mock_update.effective_user.id = 99999
        mock_update.message.text = "Hello"

        await bot.handle_message(mock_update, MagicMock())

        mock_update.message.reply_text.assert_called_once_with(
            "Unauthorized.", parse_mode="HTML"
        )

    @pytest.mark.asyncio
    async def test_message_sends_typing(self, bot: TelegramBot, mock_update):
        mock_update.message.text = "Hello"

        with patch.object(bot.claude_client, "chat", return_value=("Hi there!", [])):
            await bot.handle_message(mock_update, MagicMock())
            await bot.wait_for_processing(mock_update.effective_user.id)

        mock_update.message.chat.send_action.assert_called_once_with("typing")

    @pytest.mark.asyncio
    async def test_message_calls_claude(self, bot: TelegramBot, mock_update):
        mock_update.message.text = "What's in my folder?"

        with patch.object(
            bot.claude_client, "chat", return_value=("Your folder contains...", [])
        ) as mock_chat:
            await bot.handle_message(mock_update, MagicMock())
            await bot.wait_for_processing(mock_update.effective_user.id)

        mock_chat.assert_called_once()
        call_args = mock_chat.call_args
        assert call_args[0][0] == "What's in my folder?"

    @pytest.mark.asyncio
    async def test_message_stores_history(self, bot: TelegramBot, mock_update):
        mock_update.message.text = "Hello"

        with patch.object(bot.claude_client, "chat", return_value=("Hi there!", [])):
            await bot.handle_message(mock_update, MagicMock())
            await bot.wait_for_processing(mock_update.effective_user.id)

        history = bot.session_manager.get_history(12345)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Hi there!"

    @pytest.mark.asyncio
    async def test_message_logs_conversation(
        self, bot: TelegramBot, mock_update, mock_config: Config
    ):
        mock_update.message.text = "Hello"
        log_folder = mock_config.root_folder / "logs"

        with patch.object(bot.claude_client, "chat", return_value=("Hi there!", [])):
            await bot.handle_message(mock_update, MagicMock())
            await bot.wait_for_processing(mock_update.effective_user.id)

        # Check that log file was created
        log_files = list(log_folder.glob("*.md"))
        assert len(log_files) == 1

        log_content = log_files[0].read_text()
        assert "Hello" in log_content
        assert "Hi there!" in log_content

    @pytest.mark.asyncio
    async def test_long_response_split(self, bot: TelegramBot, mock_update):
        mock_update.message.text = "Tell me everything"
        long_response = "x" * 5000  # Longer than Telegram's 4096 limit

        # Mark user as already notified about current version
        from folderbot import __version__

        bot.session_manager.set_last_notified_version(
            mock_update.effective_user.id, __version__
        )

        with patch.object(bot.claude_client, "chat", return_value=(long_response, [])):
            await bot.handle_message(mock_update, MagicMock())
            await bot.wait_for_processing(mock_update.effective_user.id)

        # Should be called 2 times for split message
        assert mock_update.message.reply_text.call_count == 2

    @pytest.mark.asyncio
    async def test_error_handling(self, bot: TelegramBot, mock_update):
        mock_update.message.text = "Hello"

        with patch.object(
            bot.claude_client, "chat", side_effect=Exception("API Error")
        ):
            await bot.handle_message(mock_update, MagicMock())
            await bot.wait_for_processing(mock_update.effective_user.id)

        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Error:" in call_args

    @pytest.mark.asyncio
    async def test_anthropic_500_error_shows_friendly_message(
        self, bot: TelegramBot, mock_update
    ):
        """Test that Anthropic 500 errors show a friendly message, not raw error."""
        mock_update.message.text = "Hello"

        # Simulate Anthropic 500 Internal Server Error
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.headers = {}
        api_error = APIStatusError(
            message="Internal server error",
            response=mock_response,
            body={
                "type": "error",
                "error": {"type": "api_error", "message": "Internal server error"},
            },
        )

        with patch.object(bot.claude_client, "chat", side_effect=api_error):
            await bot.handle_message(mock_update, MagicMock())
            await bot.wait_for_processing(mock_update.effective_user.id)

        call_args = mock_update.message.reply_text.call_args[0][0]
        # Should show friendly message, not raw error details
        assert (
            "temporarily unavailable" in call_args.lower()
            or "try again" in call_args.lower()
        )
        # Should NOT show raw error JSON or status code
        assert "500" not in call_args
        assert "api_error" not in call_args

    @pytest.mark.asyncio
    async def test_anthropic_rate_limit_error_shows_friendly_message(
        self, bot: TelegramBot, mock_update
    ):
        """Test that Anthropic rate limit errors show a friendly message."""
        mock_update.message.text = "Hello"

        # Simulate Anthropic 429 Rate Limit Error
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 429
        mock_response.headers = {}
        api_error = APIStatusError(
            message="Rate limit exceeded",
            response=mock_response,
            body={"type": "error", "error": {"type": "rate_limit_error"}},
        )

        with patch.object(bot.claude_client, "chat", side_effect=api_error):
            await bot.handle_message(mock_update, MagicMock())
            await bot.wait_for_processing(mock_update.effective_user.id)

        call_args = mock_update.message.reply_text.call_args[0][0]
        # Should show friendly message, NOT the raw "Rate limit exceeded"
        assert "429" not in call_args
        assert "rate_limit_error" not in call_args.lower()
        # Must contain user-friendly phrasing
        assert "try again" in call_args.lower() or "moment" in call_args.lower()


class TestHtmlFormatting:
    @pytest.mark.asyncio
    async def test_reply_text_uses_html_parse_mode(self, bot: TelegramBot, mock_update):
        """Messages should be sent with parse_mode=HTML."""
        await bot.start_command(mock_update, MagicMock())

        mock_update.message.reply_text.assert_called_once()
        assert mock_update.message.reply_text.call_args.kwargs["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_reply_text_falls_back_to_plain_on_bad_html(
        self, bot: TelegramBot, mock_update
    ):
        """If HTML parsing fails, message should be resent as plain text."""
        from telegram.error import BadRequest

        # First call (with HTML) raises BadRequest, second (plain) succeeds
        mock_update.message.reply_text.side_effect = [
            BadRequest("Can't parse entities"),
            None,
        ]

        mock_update.effective_user.id = 99999
        mock_update.message.text = "Hello"
        await bot.handle_message(mock_update, MagicMock())

        assert mock_update.message.reply_text.call_count == 2
        # First attempt with HTML
        first_call = mock_update.message.reply_text.call_args_list[0]
        assert first_call == call("Unauthorized.", parse_mode="HTML")
        # Fallback without parse_mode
        second_call = mock_update.message.reply_text.call_args_list[1]
        assert second_call == call("Unauthorized.")

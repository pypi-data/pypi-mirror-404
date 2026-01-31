"""Tests for session manager."""

from pathlib import Path

import pytest

from folderbot.session_manager import SessionManager


@pytest.fixture
def session_manager(tmp_path: Path) -> SessionManager:
    """Create a session manager with a temporary database."""
    db_path = tmp_path / "test_sessions.db"
    return SessionManager(db_path)


class TestSessionManager:
    def test_creates_database(self, tmp_path: Path):
        db_path = tmp_path / "subdir" / "sessions.db"
        SessionManager(db_path)  # Creates DB on init

        assert db_path.exists()
        assert db_path.parent.exists()

    def test_empty_history_for_new_user(self, session_manager: SessionManager):
        history = session_manager.get_history(user_id=12345)

        assert history == []

    def test_add_single_message(self, session_manager: SessionManager):
        session_manager.add_message(user_id=12345, role="user", content="Hello")

        history = session_manager.get_history(user_id=12345)

        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert "timestamp" in history[0]

    def test_add_multiple_messages(self, session_manager: SessionManager):
        session_manager.add_message(user_id=12345, role="user", content="Hello")
        session_manager.add_message(
            user_id=12345, role="assistant", content="Hi there!"
        )
        session_manager.add_message(user_id=12345, role="user", content="How are you?")

        history = session_manager.get_history(user_id=12345)

        assert len(history) == 3
        assert history[0]["content"] == "Hello"
        assert history[1]["content"] == "Hi there!"
        assert history[2]["content"] == "How are you?"

    def test_separate_user_sessions(self, session_manager: SessionManager):
        session_manager.add_message(user_id=111, role="user", content="User 1 message")
        session_manager.add_message(user_id=222, role="user", content="User 2 message")

        history_1 = session_manager.get_history(user_id=111)
        history_2 = session_manager.get_history(user_id=222)

        assert len(history_1) == 1
        assert len(history_2) == 1
        assert history_1[0]["content"] == "User 1 message"
        assert history_2[0]["content"] == "User 2 message"

    def test_clear_session(self, session_manager: SessionManager):
        session_manager.add_message(user_id=12345, role="user", content="Hello")
        session_manager.add_message(user_id=12345, role="assistant", content="Hi!")

        session_manager.clear_session(user_id=12345)

        history = session_manager.get_history(user_id=12345)
        assert history == []

    def test_clear_session_only_affects_specific_user(
        self, session_manager: SessionManager
    ):
        session_manager.add_message(user_id=111, role="user", content="User 1")
        session_manager.add_message(user_id=222, role="user", content="User 2")

        session_manager.clear_session(user_id=111)

        assert session_manager.get_history(user_id=111) == []
        assert len(session_manager.get_history(user_id=222)) == 1

    def test_get_session_info_new_user(self, session_manager: SessionManager):
        info = session_manager.get_session_info(user_id=99999)

        assert info["message_count"] == 0
        assert info["created_at"] is None
        assert info["updated_at"] is None

    def test_get_session_info_existing_user(self, session_manager: SessionManager):
        session_manager.add_message(user_id=12345, role="user", content="Hello")
        session_manager.add_message(user_id=12345, role="assistant", content="Hi!")

        info = session_manager.get_session_info(user_id=12345)

        assert info["message_count"] == 2
        assert info["created_at"] is not None
        assert info["updated_at"] is not None

    def test_session_info_after_clear(self, session_manager: SessionManager):
        session_manager.add_message(user_id=12345, role="user", content="Hello")
        session_manager.clear_session(user_id=12345)

        info = session_manager.get_session_info(user_id=12345)

        assert info["message_count"] == 0
        # Timestamps should still exist after clear
        assert info["updated_at"] is not None

    def test_persistence_across_instances(self, tmp_path: Path):
        db_path = tmp_path / "persistent.db"

        # First instance
        manager1 = SessionManager(db_path)
        manager1.add_message(user_id=12345, role="user", content="Persistent message")

        # Second instance with same db
        manager2 = SessionManager(db_path)
        history = manager2.get_history(user_id=12345)

        assert len(history) == 1
        assert history[0]["content"] == "Persistent message"

    def test_unicode_content(self, session_manager: SessionManager):
        session_manager.add_message(
            user_id=12345, role="user", content="Hello 你好 مرحبا 🎉"
        )

        history = session_manager.get_history(user_id=12345)

        assert history[0]["content"] == "Hello 你好 مرحبا 🎉"

    def test_long_content(self, session_manager: SessionManager):
        long_content = "x" * 10000
        session_manager.add_message(user_id=12345, role="user", content=long_content)

        history = session_manager.get_history(user_id=12345)

        assert history[0]["content"] == long_content

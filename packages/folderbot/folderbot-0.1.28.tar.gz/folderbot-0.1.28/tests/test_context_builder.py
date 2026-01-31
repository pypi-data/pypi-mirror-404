"""Tests for context builder."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from folderbot.config import Config, ReadRules
from folderbot.context_builder import ContextBuilder


@pytest.fixture
def mock_config(tmp_path: Path) -> Config:
    """Create a mock config for testing."""
    config = MagicMock(spec=Config)
    config.root_folder = tmp_path
    config.read_rules = ReadRules(
        include=["**/*.md", "**/*.txt"],
        exclude=["excluded/**", ".git/**"],
    )
    config.max_context_chars = 10000
    return config


@pytest.fixture
def sample_folder(tmp_path: Path) -> Path:
    """Create a sample folder structure for testing."""
    # Create some markdown files
    (tmp_path / "readme.md").write_text("# Main readme\nThis is the main file.")
    (tmp_path / "notes.txt").write_text("Some notes here.")

    # Create a subfolder with files
    subfolder = tmp_path / "subfolder"
    subfolder.mkdir()
    (subfolder / "doc.md").write_text("# Subfolder doc\nMore content.")

    # Create an excluded folder
    excluded = tmp_path / "excluded"
    excluded.mkdir()
    (excluded / "secret.md").write_text("This should be excluded.")

    # Create a non-matching file
    (tmp_path / "data.json").write_text('{"key": "value"}')

    return tmp_path


class TestContextBuilder:
    def test_get_matching_files(self, mock_config: Config, sample_folder: Path):
        mock_config.root_folder = sample_folder
        builder = ContextBuilder(mock_config)

        files = builder._get_matching_files()
        file_names = [f.name for f in files]

        assert "readme.md" in file_names
        assert "notes.txt" in file_names
        assert "doc.md" in file_names
        assert "secret.md" not in file_names  # excluded
        assert "data.json" not in file_names  # not in include patterns

    def test_build_context_includes_file_content(
        self, mock_config: Config, sample_folder: Path
    ):
        mock_config.root_folder = sample_folder
        builder = ContextBuilder(mock_config)

        context = builder.build_context()

        assert "# Main readme" in context
        assert "Some notes here." in context
        assert "# Subfolder doc" in context
        assert "This should be excluded" not in context

    def test_build_context_includes_file_paths(
        self, mock_config: Config, sample_folder: Path
    ):
        mock_config.root_folder = sample_folder
        builder = ContextBuilder(mock_config)

        context = builder.build_context()

        assert "readme.md" in context
        assert "notes.txt" in context

    def test_get_file_list(self, mock_config: Config, sample_folder: Path):
        mock_config.root_folder = sample_folder
        builder = ContextBuilder(mock_config)

        file_list = builder.get_file_list()

        assert "readme.md" in file_list
        assert "notes.txt" in file_list
        assert any("doc.md" in f for f in file_list)

    def test_get_context_stats(self, mock_config: Config, sample_folder: Path):
        mock_config.root_folder = sample_folder
        builder = ContextBuilder(mock_config)

        stats = builder.get_context_stats()

        assert stats["file_count"] == 3  # readme.md, notes.txt, subfolder/doc.md
        assert stats["total_chars"] > 0
        assert "cache_age_seconds" in stats

    def test_context_truncation(self, mock_config: Config, sample_folder: Path):
        mock_config.root_folder = sample_folder
        mock_config.max_context_chars = 50  # Very small limit
        builder = ContextBuilder(mock_config)

        context = builder.build_context()

        assert len(context) <= 100  # Some buffer for truncation message
        assert "truncated" in context.lower() or len(context) <= 50

    def test_empty_folder(self, mock_config: Config, tmp_path: Path):
        mock_config.root_folder = tmp_path
        builder = ContextBuilder(mock_config)

        context = builder.build_context()
        file_list = builder.get_file_list()
        stats = builder.get_context_stats()

        assert context == ""
        assert file_list == []
        assert stats["file_count"] == 0

    def test_cache_refresh(self, mock_config: Config, sample_folder: Path):
        mock_config.root_folder = sample_folder
        builder = ContextBuilder(mock_config)

        # First call populates cache
        files1 = builder.get_file_list()

        # Add a new file
        (sample_folder / "new_file.md").write_text("New content")

        # Force cache refresh
        builder._cache_time = 0
        files2 = builder.get_file_list()

        assert "new_file.md" in files2
        assert len(files2) == len(files1) + 1

    def test_reads_from_configured_folder_not_site_packages(
        self, mock_config: Config, tmp_path: Path
    ):
        """Verify context is built from config.root_folder, not hardcoded paths."""
        # Create a unique file in our test folder
        unique_content = "UNIQUE_TEST_MARKER_12345"
        (tmp_path / "test_file.md").write_text(unique_content)

        mock_config.root_folder = tmp_path
        builder = ContextBuilder(mock_config)

        context = builder.build_context()

        # The unique content should be in the context
        assert unique_content in context
        # Should not contain anything from site-packages
        assert "site-packages" not in context

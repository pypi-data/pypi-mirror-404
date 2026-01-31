"""Build context from folder files for Claude."""

import time
from pathlib import Path

import pathspec

from .config import Config


class ContextBuilder:
    """Reads files from the folder and builds context for Claude."""

    def __init__(self, config: Config):
        self.config = config
        self._cache: dict[str, str] = {}
        self._cache_time: float = 0
        self._cache_ttl: float = 60.0  # Refresh cache every 60 seconds

    def _should_refresh_cache(self) -> bool:
        return time.time() - self._cache_time > self._cache_ttl

    def _build_spec(self, patterns: list[str]) -> pathspec.PathSpec:
        """Build a pathspec from glob patterns."""
        return pathspec.PathSpec.from_lines("gitignore", patterns)

    def _get_matching_files(self) -> list[Path]:
        """Get all files matching include patterns but not exclude patterns."""
        root = self.config.root_folder
        include_spec = self._build_spec(self.config.read_rules.include)
        exclude_spec = self._build_spec(self.config.read_rules.exclude)

        matching_files: list[Path] = []

        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue

            # Get relative path for pattern matching
            try:
                rel_path = file_path.relative_to(root)
            except ValueError:
                continue

            rel_str = str(rel_path)

            # Check if included and not excluded
            if include_spec.match_file(rel_str) and not exclude_spec.match_file(
                rel_str
            ):
                matching_files.append(file_path)

        # Sort by modification time (most recent first)
        matching_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return matching_files

    def _read_file_safe(self, file_path: Path) -> str | None:
        """Read a file, returning None if it fails."""
        try:
            return file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None

    def build_context(self) -> str:
        """Build the full context string from all matching files."""
        if self._should_refresh_cache():
            self._refresh_cache()

        parts: list[str] = []
        total_chars = 0
        max_chars = self.config.max_context_chars

        for rel_path, content in self._cache.items():
            # Check if adding this file would exceed limit
            file_block = f"## {rel_path}\n\n{content}\n\n"
            if total_chars + len(file_block) > max_chars:
                # Add truncation notice and stop
                parts.append(
                    f"\n[Context truncated at {max_chars} chars. {len(self._cache) - len(parts)} files omitted.]"
                )
                break

            parts.append(file_block)
            total_chars += len(file_block)

        return "".join(parts)

    def _refresh_cache(self) -> None:
        """Refresh the file cache."""
        self._cache.clear()
        files = self._get_matching_files()

        for file_path in files:
            content = self._read_file_safe(file_path)
            if content:
                rel_path = str(file_path.relative_to(self.config.root_folder))
                self._cache[rel_path] = content

        self._cache_time = time.time()

    def get_file_list(self) -> list[str]:
        """Get list of files included in context."""
        if self._should_refresh_cache():
            self._refresh_cache()
        return list(self._cache.keys())

    def get_context_stats(self) -> dict:
        """Get statistics about the current context."""
        if self._should_refresh_cache():
            self._refresh_cache()

        total_chars = sum(len(c) for c in self._cache.values())
        return {
            "file_count": len(self._cache),
            "total_chars": total_chars,
            "cache_age_seconds": int(time.time() - self._cache_time),
        }

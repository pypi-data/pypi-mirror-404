"""Configuration loading for self-bot."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


# Default values for read rules
DEFAULT_INCLUDE_PATTERNS = ["**/*.md", "**/*.txt"]
DEFAULT_EXCLUDE_PATTERNS = ["**/docs/**", "folderbot/**", ".git/**"]
DEFAULT_APPEND_ALLOWED_PATTERNS = ["logs/*.md", "**/todo.md", "**/todos.md"]

# Default values for file watching
DEFAULT_WATCH_INCLUDE = ["**/*.md"]
DEFAULT_WATCH_EXCLUDE = [".git/**", ".folderbot/**", "**/__pycache__/**", "**/*.pyc"]


@dataclass
class WatchConfig:
    """Configuration for file change watching.

    The watcher is always running, but notifications are per-user
    and controlled via enable_file_notifications/disable_file_notifications tools.
    """

    include: list[str] = field(default_factory=lambda: DEFAULT_WATCH_INCLUDE.copy())
    exclude: list[str] = field(default_factory=lambda: DEFAULT_WATCH_EXCLUDE.copy())
    debounce_seconds: float = 2.0


@dataclass
class ReadRules:
    include: list[str] = field(default_factory=lambda: DEFAULT_INCLUDE_PATTERNS.copy())
    exclude: list[str] = field(default_factory=lambda: DEFAULT_EXCLUDE_PATTERNS.copy())
    append_allowed: list[str] = field(
        default_factory=lambda: DEFAULT_APPEND_ALLOWED_PATTERNS.copy()
    )


@dataclass
class Config:
    telegram_token: str
    anthropic_api_key: str
    root_folder: Path
    allowed_user_ids: list[int]
    user_name: str = "User"
    read_rules: ReadRules = field(default_factory=ReadRules)
    watch_config: WatchConfig = field(default_factory=WatchConfig)
    auto_log_folder: str = "logs/"
    db_path: Path = field(default_factory=lambda: Path(".folderbot/sessions.db"))
    model: str = "claude-sonnet-4-20250514"
    max_context_chars: int = 100_000

    @classmethod
    def load(
        cls, config_path: Optional[Path] = None, bot_name: Optional[str] = None
    ) -> "Config":
        """Load config from YAML file and/or environment variables.

        Args:
            config_path: Path to config file. Defaults to ~/.config/folderbot/config.yaml
            bot_name: Name of bot to load (for multi-bot configs). If None and config
                      has multiple bots, raises an error. If config has only one bot,
                      it's selected automatically.
        """
        raw_config: dict[str, Any] = {}

        # Try loading from YAML file
        if config_path is None:
            config_path = Path.home() / ".config" / "folderbot" / "config.yaml"

        if config_path.exists():
            with open(config_path) as f:
                raw_config = yaml.safe_load(f) or {}

        # Determine effective config (handle multi-bot structure)
        config_data = cls._resolve_bot_config(raw_config, bot_name)

        # Environment variables override YAML
        telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN") or config_data.get(
            "telegram_token"
        )
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY") or config_data.get(
            "anthropic_api_key"
        )

        if not telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set (env var or config.yaml)")
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set (env var or config.yaml)")

        # Root folder
        root_folder_str = os.environ.get("SELF_BOT_ROOT") or config_data.get(
            "root_folder"
        )
        if root_folder_str:
            root_folder = Path(root_folder_str).expanduser().resolve()
        else:
            root_folder = Path.cwd()

        # Allowed user IDs
        allowed_ids_str = os.environ.get("SELF_BOT_ALLOWED_IDS")
        if allowed_ids_str:
            allowed_user_ids = [int(x.strip()) for x in allowed_ids_str.split(",")]
        else:
            allowed_user_ids = config_data.get("allowed_user_ids", [])

        if not allowed_user_ids:
            raise ValueError("No allowed_user_ids configured")

        # Read rules
        read_rules_data = config_data.get("read_rules", {})
        read_rules = ReadRules(
            include=read_rules_data.get("include", DEFAULT_INCLUDE_PATTERNS.copy()),
            exclude=read_rules_data.get("exclude", DEFAULT_EXCLUDE_PATTERNS.copy()),
            append_allowed=read_rules_data.get(
                "append_allowed", DEFAULT_APPEND_ALLOWED_PATTERNS.copy()
            ),
        )

        # Watch config
        watch_data = config_data.get("watch", {})
        watch_config = WatchConfig(
            include=watch_data.get("include", DEFAULT_WATCH_INCLUDE.copy()),
            exclude=watch_data.get("exclude", DEFAULT_WATCH_EXCLUDE.copy()),
            debounce_seconds=watch_data.get("debounce_seconds", 2.0),
        )

        # Other settings
        user_name = config_data.get("user_name", "User")
        auto_log_folder = config_data.get("auto_log_folder", "logs/")

        db_path_str = os.environ.get("SELF_BOT_DB_PATH") or config_data.get("db_path")
        if db_path_str:
            db_path = Path(db_path_str).expanduser()
        else:
            db_path = root_folder / ".folderbot" / "sessions.db"

        model = os.environ.get("SELF_BOT_MODEL") or config_data.get(
            "model", "claude-sonnet-4-20250514"
        )
        max_context_chars = config_data.get("max_context_chars", 100_000)

        return cls(
            telegram_token=telegram_token,
            anthropic_api_key=anthropic_api_key,
            root_folder=root_folder,
            allowed_user_ids=allowed_user_ids,
            user_name=user_name,
            read_rules=read_rules,
            watch_config=watch_config,
            auto_log_folder=auto_log_folder,
            db_path=db_path,
            model=model,
            max_context_chars=max_context_chars,
        )

    @classmethod
    def _resolve_bot_config(
        cls, raw_config: dict[str, Any], bot_name: Optional[str]
    ) -> dict[str, Any]:
        """Resolve the effective config, handling multi-bot structure.

        If raw_config has a 'bots' section, merge global settings with bot-specific.
        Otherwise, return raw_config as-is (backward compatible flat format).
        """
        bots = raw_config.get("bots")

        if not bots:
            # Flat config format (backward compatible)
            return raw_config

        # Multi-bot config format
        if bot_name:
            if bot_name not in bots:
                available = ", ".join(bots.keys())
                raise ValueError(
                    f"Bot '{bot_name}' not found in config. Available bots: {available}"
                )
            selected_bot = bot_name
        elif len(bots) == 1:
            # Auto-select the only bot
            selected_bot = next(iter(bots.keys()))
        else:
            # Multiple bots, need to specify which one
            available = ", ".join(bots.keys())
            raise ValueError(
                f"Config has multiple bots. Please specify which bot to run: {available}"
            )

        # Merge global settings with bot-specific settings
        # Bot settings override global settings
        bot_config: dict[str, Any] = bots[selected_bot]
        merged: dict[str, Any] = {}

        # Copy global settings (excluding 'bots' key)
        for key, value in raw_config.items():
            if key != "bots":
                merged[key] = value

        # Override with bot-specific settings
        for key, value in bot_config.items():
            merged[key] = value

        return merged

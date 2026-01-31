"""Tests for configuration loading."""

from pathlib import Path

import pytest
import yaml

from folderbot.config import Config, ReadRules


class TestReadRules:
    def test_default_values(self):
        rules = ReadRules()
        assert "**/*.md" in rules.include
        assert "**/*.txt" in rules.include
        assert ".git/**" in rules.exclude

    def test_custom_values(self):
        rules = ReadRules(include=["*.py"], exclude=["test_*"])
        assert rules.include == ["*.py"]
        assert rules.exclude == ["test_*"]


class TestConfig:
    def test_load_from_yaml(self, tmp_path: Path):
        config_data = {
            "telegram_token": "test_token_123",
            "anthropic_api_key": "test_api_key_456",
            "allowed_user_ids": [12345],
            "root_folder": str(tmp_path),
        }

        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        config = Config.load(config_file)

        assert config.telegram_token == "test_token_123"
        assert config.anthropic_api_key == "test_api_key_456"
        assert config.allowed_user_ids == [12345]
        assert config.root_folder == tmp_path

    def test_load_from_env_vars(self, tmp_path: Path, monkeypatch):
        # Create minimal config file
        config_data = {"allowed_user_ids": [99999]}
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        # Set env vars
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "env_token")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env_api_key")

        config = Config.load(config_file)

        assert config.telegram_token == "env_token"
        assert config.anthropic_api_key == "env_api_key"

    def test_env_vars_override_yaml(self, tmp_path: Path, monkeypatch):
        config_data = {
            "telegram_token": "yaml_token",
            "anthropic_api_key": "yaml_api_key",
            "allowed_user_ids": [12345],
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "env_token")

        config = Config.load(config_file)

        # Env var overrides yaml
        assert config.telegram_token == "env_token"
        # Yaml value used when no env var
        assert config.anthropic_api_key == "yaml_api_key"

    def test_missing_telegram_token_raises(self, tmp_path: Path):
        config_data = {
            "anthropic_api_key": "test_key",
            "allowed_user_ids": [12345],
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
            Config.load(config_file)

    def test_missing_anthropic_key_raises(self, tmp_path: Path):
        config_data = {
            "telegram_token": "test_token",
            "allowed_user_ids": [12345],
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            Config.load(config_file)

    def test_missing_allowed_user_ids_raises(self, tmp_path: Path):
        config_data = {
            "telegram_token": "test_token",
            "anthropic_api_key": "test_key",
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ValueError, match="allowed_user_ids"):
            Config.load(config_file)

    def test_custom_read_rules(self, tmp_path: Path):
        config_data = {
            "telegram_token": "test_token",
            "anthropic_api_key": "test_key",
            "allowed_user_ids": [12345],
            "read_rules": {
                "include": ["*.py", "*.md"],
                "exclude": ["__pycache__/**"],
            },
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        config = Config.load(config_file)

        assert config.read_rules.include == ["*.py", "*.md"]
        assert config.read_rules.exclude == ["__pycache__/**"]

    def test_default_model(self, tmp_path: Path):
        config_data = {
            "telegram_token": "test_token",
            "anthropic_api_key": "test_key",
            "allowed_user_ids": [12345],
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        config = Config.load(config_file)

        assert config.model == "claude-sonnet-4-20250514"

    def test_custom_model(self, tmp_path: Path):
        config_data = {
            "telegram_token": "test_token",
            "anthropic_api_key": "test_key",
            "allowed_user_ids": [12345],
            "model": "claude-3-haiku-20240307",
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        config = Config.load(config_file)

        assert config.model == "claude-3-haiku-20240307"

    def test_root_folder_defaults_to_cwd(self, tmp_path: Path, monkeypatch):
        """When root_folder is not specified, it should default to cwd, not site-packages."""
        config_data = {
            "telegram_token": "test_token",
            "anthropic_api_key": "test_key",
            "allowed_user_ids": [12345],
            # No root_folder specified
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        # Change to tmp_path to simulate user's working directory
        monkeypatch.chdir(tmp_path)

        config = Config.load(config_file)

        # Should be cwd, not some path inside site-packages
        assert config.root_folder == tmp_path
        assert "site-packages" not in str(config.root_folder)

    def test_root_folder_from_config(self, tmp_path: Path):
        """When root_folder is specified in config, it should be used."""
        target_folder = tmp_path / "my_folder"
        target_folder.mkdir()

        config_data = {
            "telegram_token": "test_token",
            "anthropic_api_key": "test_key",
            "allowed_user_ids": [12345],
            "root_folder": str(target_folder),
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        config = Config.load(config_file)

        assert config.root_folder == target_folder

    def test_root_folder_from_env_var(self, tmp_path: Path, monkeypatch):
        """SELF_BOT_ROOT env var should override config file."""
        config_folder = tmp_path / "config_folder"
        config_folder.mkdir()
        env_folder = tmp_path / "env_folder"
        env_folder.mkdir()

        config_data = {
            "telegram_token": "test_token",
            "anthropic_api_key": "test_key",
            "allowed_user_ids": [12345],
            "root_folder": str(config_folder),
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        monkeypatch.setenv("SELF_BOT_ROOT", str(env_folder))

        config = Config.load(config_file)

        # Env var should override config file
        assert config.root_folder == env_folder

    def test_root_folder_expands_tilde(self, tmp_path: Path, monkeypatch):
        """root_folder should expand ~ to home directory."""
        config_data = {
            "telegram_token": "test_token",
            "anthropic_api_key": "test_key",
            "allowed_user_ids": [12345],
            "root_folder": "~/some_folder",
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        config = Config.load(config_file)

        # Should expand ~ to actual home path
        assert "~" not in str(config.root_folder)
        assert str(Path.home()) in str(config.root_folder)

    def test_user_name_default(self, tmp_path: Path):
        """user_name should default to 'User'."""
        config_data = {
            "telegram_token": "test_token",
            "anthropic_api_key": "test_key",
            "allowed_user_ids": [12345],
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        config = Config.load(config_file)

        assert config.user_name == "User"

    def test_user_name_from_config(self, tmp_path: Path):
        """user_name should be loaded from config."""
        config_data = {
            "telegram_token": "test_token",
            "anthropic_api_key": "test_key",
            "allowed_user_ids": [12345],
            "user_name": "Alice",
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        config = Config.load(config_file)

        assert config.user_name == "Alice"


class TestMultiBotConfig:
    """Tests for global + per-bot configuration structure."""

    def test_load_bot_with_global_anthropic_key(self, tmp_path: Path):
        """Global anthropic_api_key should be used when loading a specific bot."""
        work_folder = tmp_path / "work"
        work_folder.mkdir()

        config_data = {
            "anthropic_api_key": "global_api_key",
            "bots": {
                "work": {
                    "telegram_token": "work_bot_token",
                    "root_folder": str(work_folder),
                    "allowed_user_ids": [123],
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        config = Config.load(config_file, bot_name="work")

        assert config.anthropic_api_key == "global_api_key"
        assert config.telegram_token == "work_bot_token"
        assert config.root_folder == work_folder
        assert config.allowed_user_ids == [123]

    def test_load_multiple_bots(self, tmp_path: Path):
        """Should be able to load different bots from the same config."""
        work_folder = tmp_path / "work"
        work_folder.mkdir()
        personal_folder = tmp_path / "personal"
        personal_folder.mkdir()

        config_data = {
            "anthropic_api_key": "shared_api_key",
            "bots": {
                "work": {
                    "telegram_token": "work_token",
                    "root_folder": str(work_folder),
                    "allowed_user_ids": [111],
                },
                "personal": {
                    "telegram_token": "personal_token",
                    "root_folder": str(personal_folder),
                    "allowed_user_ids": [222],
                },
            },
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        work_config = Config.load(config_file, bot_name="work")
        personal_config = Config.load(config_file, bot_name="personal")

        assert work_config.telegram_token == "work_token"
        assert work_config.root_folder == work_folder

        assert personal_config.telegram_token == "personal_token"
        assert personal_config.root_folder == personal_folder

        # Both should share the same API key
        assert work_config.anthropic_api_key == "shared_api_key"
        assert personal_config.anthropic_api_key == "shared_api_key"

    def test_bot_can_override_global_settings(self, tmp_path: Path):
        """Bot-specific settings should override global defaults."""
        folder = tmp_path / "notes"
        folder.mkdir()

        config_data = {
            "anthropic_api_key": "global_key",
            "model": "claude-sonnet-4-20250514",  # Global default
            "bots": {
                "work": {
                    "telegram_token": "token",
                    "root_folder": str(folder),
                    "allowed_user_ids": [123],
                    "model": "claude-3-haiku-20240307",  # Bot-specific override
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        config = Config.load(config_file, bot_name="work")

        assert config.model == "claude-3-haiku-20240307"

    def test_backward_compatible_with_flat_config(self, tmp_path: Path):
        """Old flat config format should still work (no bot_name needed)."""
        config_data = {
            "telegram_token": "flat_token",
            "anthropic_api_key": "flat_key",
            "allowed_user_ids": [123],
            "root_folder": str(tmp_path),
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        # Should work without specifying bot_name
        config = Config.load(config_file)

        assert config.telegram_token == "flat_token"
        assert config.anthropic_api_key == "flat_key"

    def test_error_when_bot_not_found(self, tmp_path: Path):
        """Should raise error when specified bot doesn't exist."""
        config_data = {
            "anthropic_api_key": "key",
            "bots": {
                "work": {
                    "telegram_token": "token",
                    "root_folder": str(tmp_path),
                    "allowed_user_ids": [123],
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ValueError, match="Bot 'nonexistent' not found"):
            Config.load(config_file, bot_name="nonexistent")

    def test_error_when_bots_config_but_no_bot_name(self, tmp_path: Path):
        """Should raise helpful error when config has multiple bots but no bot_name specified."""
        config_data = {
            "anthropic_api_key": "key",
            "bots": {
                "work": {
                    "telegram_token": "token1",
                    "root_folder": str(tmp_path),
                    "allowed_user_ids": [123],
                },
                "personal": {
                    "telegram_token": "token2",
                    "root_folder": str(tmp_path),
                    "allowed_user_ids": [456],
                },
            },
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ValueError, match="specify which bot"):
            Config.load(config_file)

    def test_single_bot_loads_automatically(self, tmp_path: Path):
        """When there's only one bot, it should load automatically without bot_name."""
        folder = tmp_path / "notes"
        folder.mkdir()

        config_data = {
            "anthropic_api_key": "key",
            "bots": {
                "default": {
                    "telegram_token": "token",
                    "root_folder": str(folder),
                    "allowed_user_ids": [123],
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        # Should auto-select the only bot
        config = Config.load(config_file)

        assert config.telegram_token == "token"
        assert config.root_folder == folder

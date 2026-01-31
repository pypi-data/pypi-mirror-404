"""Tests for CLI module."""

import argparse
from unittest.mock import patch, MagicMock

import yaml

from folderbot import cli
from folderbot.cli import (
    cmd_config_show,
    cmd_config_set,
    cmd_config_folder,
    cmd_init,
    cmd_status,
    cmd_run,
    cmd_service_install,
    cmd_service_uninstall,
    cmd_service_enable,
    cmd_service_disable,
    cmd_service_start,
    cmd_service_stop,
    cmd_service_restart,
    cmd_service_status,
    cmd_service_logs,
    load_config_yaml,
    save_config_yaml,
)
from folderbot.config import Config


class TestLoadSaveConfigYaml:
    def test_load_nonexistent_returns_empty(self, monkeypatch, tmp_path):
        monkeypatch.setattr(cli, "CONFIG_PATH", tmp_path / "nonexistent.yaml")
        assert load_config_yaml() == {}

    def test_load_existing_config(self, monkeypatch, tmp_path):
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({"model": "test-model"}))
        monkeypatch.setattr(cli, "CONFIG_PATH", config_path)

        assert load_config_yaml() == {"model": "test-model"}

    def test_save_config(self, monkeypatch, tmp_path):
        config_path = tmp_path / "config.yaml"
        monkeypatch.setattr(cli, "CONFIG_PATH", config_path)

        save_config_yaml({"model": "new-model", "allowed_user_ids": [123]})

        loaded = yaml.safe_load(config_path.read_text())
        assert loaded == {"model": "new-model", "allowed_user_ids": [123]}

    def test_save_config_creates_parent_directory(self, monkeypatch, tmp_path):
        """Test that save_config_yaml creates parent directories if they don't exist."""
        config_path = tmp_path / "nested" / "dir" / "config.yaml"
        monkeypatch.setattr(cli, "CONFIG_PATH", config_path)

        # Parent directory doesn't exist yet
        assert not config_path.parent.exists()

        save_config_yaml({"model": "test"})

        # Now parent should exist and file should be saved
        assert config_path.parent.exists()
        assert config_path.exists()
        loaded = yaml.safe_load(config_path.read_text())
        assert loaded == {"model": "test"}


class TestCmdConfigShow:
    def test_no_config_file(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setattr(cli, "CONFIG_PATH", tmp_path / "nonexistent.yaml")

        result = cmd_config_show(argparse.Namespace())

        assert result == 1
        assert "No configuration file found" in capsys.readouterr().out

    def test_masks_sensitive_values(self, monkeypatch, tmp_path, capsys):
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.dump(
                {
                    "telegram_token": "1234567890abcdef",
                    "anthropic_api_key": "sk-ant-key-secret123",
                }
            )
        )
        monkeypatch.setattr(cli, "CONFIG_PATH", config_path)

        cmd_config_show(argparse.Namespace())

        output = capsys.readouterr().out
        assert "1234567890abcdef" not in output  # Full token not shown
        assert "123456" in output  # Partial shown
        assert "cdef" in output


class TestCmdConfigSet:
    def test_set_simple_value(self, monkeypatch, tmp_path):
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))
        monkeypatch.setattr(cli, "CONFIG_PATH", config_path)

        cmd_config_set(argparse.Namespace(key="model", value="new-model"))

        assert yaml.safe_load(config_path.read_text())["model"] == "new-model"

    def test_set_allowed_user_ids_parses_list(self, monkeypatch, tmp_path):
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))
        monkeypatch.setattr(cli, "CONFIG_PATH", config_path)

        cmd_config_set(argparse.Namespace(key="allowed_user_ids", value="123,456"))

        assert yaml.safe_load(config_path.read_text())["allowed_user_ids"] == [123, 456]

    def test_set_nested_value(self, monkeypatch, tmp_path):
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))
        monkeypatch.setattr(cli, "CONFIG_PATH", config_path)

        cmd_config_set(argparse.Namespace(key="read_rules.include", value="*.py,*.md"))

        loaded = yaml.safe_load(config_path.read_text())
        assert loaded["read_rules"]["include"] == ["*.py", "*.md"]


class TestCmdConfigFolder:
    def test_set_existing_folder(self, monkeypatch, tmp_path):
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))
        monkeypatch.setattr(cli, "CONFIG_PATH", config_path)

        folder = tmp_path / "my_folder"
        folder.mkdir()

        result = cmd_config_folder(argparse.Namespace(path=str(folder)))

        assert result == 0
        assert yaml.safe_load(config_path.read_text())["root_folder"] == str(folder)

    def test_nonexistent_folder_rejected(self, monkeypatch, tmp_path):
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))
        monkeypatch.setattr(cli, "CONFIG_PATH", config_path)
        monkeypatch.setattr("builtins.input", lambda _: "n")

        result = cmd_config_folder(argparse.Namespace(path="/nonexistent"))

        assert result == 1


class TestCmdInit:
    def test_creates_config_with_inputs(self, monkeypatch, tmp_path):
        config_path = tmp_path / "config.yaml"
        monkeypatch.setattr(cli, "CONFIG_PATH", config_path)

        # Inputs: user_id, user_name, folder_path
        regular_inputs = iter(["123456", "TestUser", ""])
        # Getpass inputs: telegram_token, anthropic_api_key
        getpass_inputs = iter(["test_token", "test_key"])
        monkeypatch.setattr(cli, "getpass", lambda _: next(getpass_inputs))
        monkeypatch.setattr("builtins.input", lambda _: next(regular_inputs))

        result = cmd_init(argparse.Namespace())

        assert result == 0
        loaded = yaml.safe_load(config_path.read_text())
        assert loaded["telegram_token"] == "test_token"
        assert loaded["anthropic_api_key"] == "test_key"
        assert loaded["allowed_user_ids"] == [123456]
        assert loaded["user_name"] == "TestUser"

    def test_fails_without_token(self, monkeypatch, tmp_path):
        monkeypatch.setattr(cli, "CONFIG_PATH", tmp_path / "config.yaml")
        monkeypatch.setattr(cli, "getpass", lambda _: "")

        result = cmd_init(argparse.Namespace())

        assert result == 1

    def test_saves_default_folder_when_user_presses_enter(self, monkeypatch, tmp_path):
        """Test that pressing Enter for folder saves cwd to config, not leaving it empty."""
        config_path = tmp_path / "config.yaml"
        monkeypatch.setattr(cli, "CONFIG_PATH", config_path)

        # Simulate user's working directory
        work_dir = tmp_path / "my_notes"
        work_dir.mkdir()
        monkeypatch.chdir(work_dir)

        # Inputs: user_id, user_name, folder_path (empty = default)
        regular_inputs = iter(["123456", "TestUser", ""])
        getpass_inputs = iter(["test_token", "test_key"])
        monkeypatch.setattr(cli, "getpass", lambda _: next(getpass_inputs))
        monkeypatch.setattr("builtins.input", lambda _: next(regular_inputs))

        result = cmd_init(argparse.Namespace())

        assert result == 0
        loaded = yaml.safe_load(config_path.read_text())
        # root_folder should be saved explicitly, not missing
        assert "root_folder" in loaded, (
            "root_folder should be saved even when user presses Enter"
        )
        assert loaded["root_folder"] == str(work_dir)


class TestCmdStatus:
    def test_no_config(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setattr(cli, "CONFIG_PATH", tmp_path / "nonexistent.yaml")

        result = cmd_status(argparse.Namespace())

        assert result == 1
        assert "NOT CONFIGURED" in capsys.readouterr().out

    def test_with_valid_config(self, monkeypatch, tmp_path, capsys):
        config_path = tmp_path / "config.yaml"
        root_folder = tmp_path / "root"
        root_folder.mkdir()
        (root_folder / "test.md").write_text("# Test")

        config_data = {
            "telegram_token": "test_token",
            "anthropic_api_key": "test_key",
            "allowed_user_ids": [123],
            "root_folder": str(root_folder),
        }
        config_path.write_text(yaml.dump(config_data))
        monkeypatch.setattr(cli, "CONFIG_PATH", config_path)

        # Mock Config.load to use our test config
        mock_config = Config(
            telegram_token="test_token",
            anthropic_api_key="test_key",
            allowed_user_ids=[123],
            root_folder=root_folder,
        )
        monkeypatch.setattr(Config, "load", lambda path=None: mock_config)

        result = cmd_status(argparse.Namespace())

        assert result == 0
        output = capsys.readouterr().out
        assert "Status: OK" in output
        assert "Files in context:" in output


class TestCmdRun:
    def test_invalid_config_fails(self, monkeypatch, tmp_path, capsys):
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))
        monkeypatch.setattr(cli, "CONFIG_PATH", config_path)

        def raise_error(path=None, bot_name=None):
            raise ValueError("TELEGRAM_BOT_TOKEN not set")

        monkeypatch.setattr(Config, "load", raise_error)

        result = cmd_run(argparse.Namespace(bot=None))

        assert result == 1
        assert "Configuration error" in capsys.readouterr().err

    def test_valid_config_starts_bot(self, monkeypatch, tmp_path):
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.dump(
                {
                    "telegram_token": "test",
                    "anthropic_api_key": "test",
                    "allowed_user_ids": [123],
                    "root_folder": str(tmp_path),
                }
            )
        )
        monkeypatch.setattr(cli, "CONFIG_PATH", config_path)

        mock_config = Config(
            telegram_token="test",
            anthropic_api_key="test",
            allowed_user_ids=[123],
            root_folder=tmp_path,
        )
        monkeypatch.setattr(
            Config, "load", lambda path=None, bot_name=None: mock_config
        )

        mock_bot = MagicMock()
        with patch("folderbot.telegram_handler.TelegramBot", return_value=mock_bot):
            result = cmd_run(argparse.Namespace(bot=None))

        assert result == 0
        mock_bot.run.assert_called_once()

    def test_run_with_bot_argument(self, monkeypatch, tmp_path):
        """Test that --bot argument is passed to Config.load."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.dump(
                {
                    "anthropic_api_key": "test_key",
                    "bots": {
                        "work": {
                            "telegram_token": "work_token",
                            "allowed_user_ids": [123],
                            "root_folder": str(tmp_path),
                        }
                    },
                }
            )
        )
        monkeypatch.setattr(cli, "CONFIG_PATH", config_path)

        # Track what arguments Config.load was called with
        load_calls = []

        def mock_load(path=None, bot_name=None):
            load_calls.append({"path": path, "bot_name": bot_name})
            return Config(
                telegram_token="work_token",
                anthropic_api_key="test_key",
                allowed_user_ids=[123],
                root_folder=tmp_path,
            )

        monkeypatch.setattr(Config, "load", mock_load)

        mock_bot = MagicMock()
        with patch("folderbot.telegram_handler.TelegramBot", return_value=mock_bot):
            result = cmd_run(argparse.Namespace(bot="work"))

        assert result == 0
        assert len(load_calls) == 1
        assert load_calls[0]["bot_name"] == "work"


class TestServiceInstall:
    def test_install_creates_service_file(self, monkeypatch, tmp_path, capsys):
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.dump(
                {
                    "telegram_token": "test",
                    "anthropic_api_key": "test",
                    "allowed_user_ids": [123],
                    "root_folder": str(tmp_path),
                }
            )
        )
        monkeypatch.setattr(cli, "CONFIG_PATH", config_path)

        service_path = tmp_path / "folderbot.service"
        monkeypatch.setattr(cli, "_get_service_path", lambda: service_path)
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/folderbot")
        monkeypatch.setattr(cli, "_run_systemctl", lambda *args: (0, ""))

        # Mock subprocess.run for linger check
        mock_result = MagicMock()
        mock_result.stdout = "Linger=yes"
        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        result = cmd_service_install(argparse.Namespace())

        assert result == 0
        assert service_path.exists()
        content = service_path.read_text()
        assert "ExecStart=/usr/bin/folderbot run" in content
        assert f"WorkingDirectory={tmp_path}" in content

    def test_install_fails_without_config(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setattr(cli, "CONFIG_PATH", tmp_path / "nonexistent.yaml")
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/folderbot")

        result = cmd_service_install(argparse.Namespace())

        assert result == 1
        assert "No configuration found" in capsys.readouterr().err

    def test_install_fails_without_folderbot_in_path(
        self, monkeypatch, tmp_path, capsys
    ):
        monkeypatch.setattr("shutil.which", lambda _: None)

        result = cmd_service_install(argparse.Namespace())

        assert result == 1
        assert "'folderbot' not found" in capsys.readouterr().err


class TestServiceUninstall:
    def test_uninstall_removes_service_file(self, monkeypatch, tmp_path, capsys):
        service_path = tmp_path / "folderbot.service"
        service_path.write_text("[Unit]\nDescription=Test")
        monkeypatch.setattr(cli, "_get_service_path", lambda: service_path)
        monkeypatch.setattr(cli, "_run_systemctl", lambda *args: (0, ""))

        result = cmd_service_uninstall(argparse.Namespace())

        assert result == 0
        assert not service_path.exists()
        assert "Service uninstalled" in capsys.readouterr().out

    def test_uninstall_when_not_installed(self, monkeypatch, tmp_path, capsys):
        service_path = tmp_path / "nonexistent.service"
        monkeypatch.setattr(cli, "_get_service_path", lambda: service_path)

        result = cmd_service_uninstall(argparse.Namespace())

        assert result == 0
        assert "not installed" in capsys.readouterr().out


class TestServiceEnable:
    def test_enable_calls_systemctl(self, monkeypatch, tmp_path, capsys):
        service_path = tmp_path / "folderbot.service"
        service_path.write_text("[Unit]\nDescription=Test")
        monkeypatch.setattr(cli, "_get_service_path", lambda: service_path)

        called_with = []
        monkeypatch.setattr(
            cli, "_run_systemctl", lambda *args: (called_with.append(args), (0, ""))[1]
        )

        result = cmd_service_enable(argparse.Namespace())

        assert result == 0
        assert ("enable", "folderbot") in called_with
        assert "enabled" in capsys.readouterr().out

    def test_enable_fails_without_service(self, monkeypatch, tmp_path, capsys):
        service_path = tmp_path / "nonexistent.service"
        monkeypatch.setattr(cli, "_get_service_path", lambda: service_path)

        result = cmd_service_enable(argparse.Namespace())

        assert result == 1
        assert "not installed" in capsys.readouterr().out


class TestServiceDisable:
    def test_disable_calls_systemctl(self, monkeypatch, capsys):
        called_with = []
        monkeypatch.setattr(
            cli, "_run_systemctl", lambda *args: (called_with.append(args), (0, ""))[1]
        )

        result = cmd_service_disable(argparse.Namespace())

        assert result == 0
        assert ("disable", "folderbot") in called_with
        assert "disabled" in capsys.readouterr().out


class TestServiceStart:
    def test_start_calls_systemctl(self, monkeypatch, tmp_path, capsys):
        service_path = tmp_path / "folderbot.service"
        service_path.write_text("[Unit]\nDescription=Test")
        monkeypatch.setattr(cli, "_get_service_path", lambda: service_path)

        called_with = []
        monkeypatch.setattr(
            cli, "_run_systemctl", lambda *args: (called_with.append(args), (0, ""))[1]
        )

        result = cmd_service_start(argparse.Namespace())

        assert result == 0
        assert ("start", "folderbot") in called_with
        assert "started" in capsys.readouterr().out

    def test_start_fails_without_service(self, monkeypatch, tmp_path, capsys):
        service_path = tmp_path / "nonexistent.service"
        monkeypatch.setattr(cli, "_get_service_path", lambda: service_path)

        result = cmd_service_start(argparse.Namespace())

        assert result == 1
        assert "not installed" in capsys.readouterr().out


class TestServiceStop:
    def test_stop_calls_systemctl(self, monkeypatch, capsys):
        called_with = []
        monkeypatch.setattr(
            cli, "_run_systemctl", lambda *args: (called_with.append(args), (0, ""))[1]
        )

        result = cmd_service_stop(argparse.Namespace())

        assert result == 0
        assert ("stop", "folderbot") in called_with
        assert "stopped" in capsys.readouterr().out


class TestServiceRestart:
    def test_restart_calls_systemctl(self, monkeypatch, tmp_path, capsys):
        service_path = tmp_path / "folderbot.service"
        service_path.write_text("[Unit]\nDescription=Test")
        monkeypatch.setattr(cli, "_get_service_path", lambda: service_path)

        called_with = []
        monkeypatch.setattr(
            cli, "_run_systemctl", lambda *args: (called_with.append(args), (0, ""))[1]
        )

        result = cmd_service_restart(argparse.Namespace())

        assert result == 0
        assert ("restart", "folderbot") in called_with
        assert "restarted" in capsys.readouterr().out


class TestServiceStatus:
    def test_status_when_not_installed(self, monkeypatch, tmp_path, capsys):
        service_path = tmp_path / "nonexistent.service"
        monkeypatch.setattr(cli, "_get_service_path", lambda: service_path)

        result = cmd_service_status(argparse.Namespace())

        assert result == 0
        output = capsys.readouterr().out
        assert "not installed" in output

    def test_status_when_installed(self, monkeypatch, tmp_path, capsys):
        service_path = tmp_path / "folderbot.service"
        service_path.write_text("[Unit]\nDescription=Test")
        monkeypatch.setattr(cli, "_get_service_path", lambda: service_path)
        monkeypatch.setattr(
            cli, "_run_systemctl", lambda *args: (0, "● folderbot.service - Folderbot")
        )

        result = cmd_service_status(argparse.Namespace())

        assert result == 0
        assert "folderbot.service" in capsys.readouterr().out


class TestServiceLogs:
    def test_logs_runs_journalctl(self, monkeypatch):
        import subprocess

        called_with = []

        def mock_run(cmd, *args, **kwargs):
            called_with.append(cmd)

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = cmd_service_logs(argparse.Namespace(follow=False))

        assert result == 0
        assert any("journalctl" in str(cmd) for cmd in called_with)

    def test_logs_follow_mode(self, monkeypatch):
        import subprocess

        called_with = []

        def mock_run(cmd, *args, **kwargs):
            called_with.append(cmd)

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = cmd_service_logs(argparse.Namespace(follow=True))

        assert result == 0
        assert any("-f" in cmd for cmd in called_with)

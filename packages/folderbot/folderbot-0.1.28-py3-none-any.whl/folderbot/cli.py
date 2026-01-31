"""CLI for folderbot configuration and management."""

import argparse
import os
import sys
from getpass import getpass
from pathlib import Path

import yaml

from . import __version__
from .config import Config, DEFAULT_EXCLUDE_PATTERNS, DEFAULT_INCLUDE_PATTERNS


CONFIG_PATH = Path.home() / ".config" / "folderbot" / "config.yaml"


def get_config_path() -> Path:
    """Get the path to the config file."""
    return CONFIG_PATH


def load_config_yaml() -> dict:
    """Load raw config from YAML file."""
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


def save_config_yaml(data: dict) -> None:
    """Save config to YAML file."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def cmd_init(args: argparse.Namespace) -> int:
    """Interactive setup wizard."""
    print(f"Folderbot Setup v{__version__}")
    print("=" * 40)
    print()

    config_data = load_config_yaml()

    # Telegram token
    print("Step 1: Telegram Bot Token")
    print("  Get this from @BotFather: https://t.me/BotFather")
    current = config_data.get("telegram_token", "")
    if current and current != "YOUR_TELEGRAM_BOT_TOKEN":
        print(f"  Current: {current[:10]}...{current[-4:]}")
        change = input("  Change? [y/N]: ").strip().lower()
        if change == "y":
            token = getpass("  Enter token: ").strip()
            if token:
                config_data["telegram_token"] = token
    else:
        token = getpass("  Enter token: ").strip()
        if not token:
            print("  Error: Telegram token is required")
            return 1
        config_data["telegram_token"] = token
    print()

    # Anthropic API key
    print("Step 2: Anthropic API Key")
    print("  Get this from console.anthropic.com")
    current = config_data.get("anthropic_api_key", "")
    if current and current != "YOUR_ANTHROPIC_API_KEY":
        print(f"  Current: {current[:10]}...{current[-4:]}")
        change = input("  Change? [y/N]: ").strip().lower()
        if change == "y":
            key = getpass("  Enter API key: ").strip()
            if key:
                config_data["anthropic_api_key"] = key
    else:
        key = getpass("  Enter API key: ").strip()
        if not key:
            print("  Error: Anthropic API key is required")
            return 1
        config_data["anthropic_api_key"] = key
    print()

    # Allowed user IDs
    print("Step 3: Allowed Telegram User IDs")
    print("  Get your ID from @userinfobot: https://t.me/userinfobot")
    current_ids = config_data.get("allowed_user_ids", [])
    if current_ids and current_ids != [123456789]:
        print(f"  Current: {current_ids}")
        change = input("  Change? [y/N]: ").strip().lower()
        if change == "y":
            ids_str = input("  Enter user IDs (comma-separated): ").strip()
            if ids_str:
                config_data["allowed_user_ids"] = [
                    int(x.strip()) for x in ids_str.split(",")
                ]
    else:
        ids_str = input("  Enter your user ID: ").strip()
        if not ids_str:
            print("  Error: At least one user ID is required")
            return 1
        config_data["allowed_user_ids"] = [int(x.strip()) for x in ids_str.split(",")]
    print()

    # User name
    print("Step 4: Your Name")
    print("  Used in the AI assistant's responses")
    current_name = config_data.get("user_name", "")
    if current_name:
        print(f"  Current: {current_name}")
        change = input("  Change? [y/N]: ").strip().lower()
        if change == "y":
            name = input("  Enter your name: ").strip()
            if name:
                config_data["user_name"] = name
    else:
        name = input("  Enter your name: ").strip()
        if name:
            config_data["user_name"] = name
    print()

    # Root folder
    print("Step 5: Root Folder")
    print("  The folder you want to chat about")
    current_folder = config_data.get("root_folder", "")
    default_folder = Path.cwd()
    if current_folder:
        print(f"  Current: {current_folder}")
    else:
        print(f"  Default: {default_folder}")
    folder = input("  Enter folder path (or press Enter for default): ").strip()
    if folder:
        folder_path = Path(folder).expanduser().resolve()
        if not folder_path.exists():
            print(f"  Warning: {folder_path} does not exist")
            confirm = input("  Continue anyway? [y/N]: ").strip().lower()
            if confirm != "y":
                return 1
        config_data["root_folder"] = str(folder_path)
    else:
        # Save default folder explicitly so it's not left to runtime cwd
        config_data["root_folder"] = str(default_folder)
    print()

    # Save config
    save_config_yaml(config_data)
    print(f"Configuration saved to {get_config_path()}")
    print()
    print("Run 'folderbot run' to start the bot!")
    return 0


def cmd_config_show(args: argparse.Namespace) -> int:
    """Show current configuration."""
    config_path = get_config_path()

    print(f"Config file: {config_path}")
    print(f"Exists: {config_path.exists()}")
    print()

    if not config_path.exists():
        print("No configuration file found. Run 'folderbot init' to create one.")
        return 1

    config_data = load_config_yaml()

    # Mask sensitive values
    def mask(value: str) -> str:
        if not value or len(value) < 10:
            return "***"
        return f"{value[:6]}...{value[-4:]}"

    print("Current configuration:")
    print("-" * 40)

    # Show each setting
    token = config_data.get("telegram_token", "")
    print(f"telegram_token: {mask(token)}")

    api_key = config_data.get("anthropic_api_key", "")
    print(f"anthropic_api_key: {mask(api_key)}")

    print(f"allowed_user_ids: {config_data.get('allowed_user_ids', [])}")
    print(f"user_name: {config_data.get('user_name', 'User')}")
    print(f"root_folder: {config_data.get('root_folder', '(default)')}")
    print(f"model: {config_data.get('model', 'claude-sonnet-4-20250514')}")
    print(f"max_context_chars: {config_data.get('max_context_chars', 100000)}")
    print(f"auto_log_folder: {config_data.get('auto_log_folder', 'logs/')}")
    print(
        f"db_path: {config_data.get('db_path', '~/.local/share/self-bot/sessions.db')}"
    )

    read_rules = config_data.get("read_rules", {})
    print(f"read_rules.include: {read_rules.get('include', DEFAULT_INCLUDE_PATTERNS)}")
    print(f"read_rules.exclude: {read_rules.get('exclude', DEFAULT_EXCLUDE_PATTERNS)}")

    # Show environment overrides
    print()
    print("Environment overrides:")
    print("-" * 40)
    env_vars = [
        ("TELEGRAM_BOT_TOKEN", os.environ.get("TELEGRAM_BOT_TOKEN")),
        ("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY")),
        ("SELF_BOT_ROOT", os.environ.get("SELF_BOT_ROOT")),
        ("SELF_BOT_ALLOWED_IDS", os.environ.get("SELF_BOT_ALLOWED_IDS")),
        ("SELF_BOT_MODEL", os.environ.get("SELF_BOT_MODEL")),
        ("SELF_BOT_DB_PATH", os.environ.get("SELF_BOT_DB_PATH")),
    ]
    any_set = False
    for name, value in env_vars:
        if value:
            any_set = True
            if "TOKEN" in name or "KEY" in name:
                print(f"  {name}: {mask(value)}")
            else:
                print(f"  {name}: {value}")
    if not any_set:
        print("  (none)")

    return 0


def cmd_config_set(args: argparse.Namespace) -> int:
    """Set a configuration value."""
    config_data = load_config_yaml()

    key = args.key
    value = args.value

    # Handle nested keys like read_rules.include
    if "." in key:
        parts = key.split(".", 1)
        parent = parts[0]
        child = parts[1]
        if parent not in config_data:
            config_data[parent] = {}
        # Try to parse as list if it looks like one
        if value.startswith("[") or "," in value:
            value = [v.strip().strip("\"'") for v in value.strip("[]").split(",")]
        config_data[parent][child] = value
    else:
        # Handle special types
        if key == "allowed_user_ids":
            value = [int(x.strip()) for x in value.split(",")]
        elif key == "max_context_chars":
            value = int(value)
        config_data[key] = value

    save_config_yaml(config_data)
    print(f"Set {key} = {value}")
    return 0


def cmd_config_folder(args: argparse.Namespace) -> int:
    """Set the root folder."""
    config_data = load_config_yaml()

    folder = args.path
    folder_path = Path(folder).expanduser().resolve()

    if not folder_path.exists():
        print(f"Warning: {folder_path} does not exist")
        confirm = input("Continue anyway? [y/N]: ").strip().lower()
        if confirm != "y":
            return 1

    config_data["root_folder"] = str(folder_path)
    save_config_yaml(config_data)
    print(f"Root folder set to: {folder_path}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show current status."""
    config_path = get_config_path()

    print("Folderbot Status")
    print("=" * 40)
    print()

    # Config status
    print(f"Config file: {config_path}")
    if not config_path.exists():
        print("  Status: NOT CONFIGURED")
        print("  Run 'folderbot init' to set up")
        return 1

    # Try to load full config
    try:
        config = Config.load()
        print("  Status: OK")
    except ValueError as e:
        print(f"  Status: ERROR - {e}")
        return 1

    print()

    # Folder info
    print(f"Root folder: {config.root_folder}")
    if config.root_folder.exists():
        print("  Status: EXISTS")

        # Count files that match patterns
        from .context_builder import ContextBuilder

        builder = ContextBuilder(config)
        stats = builder.get_context_stats()

        print(f"  Files in context: {stats['file_count']}")
        print(f"  Total chars: {stats['total_chars']:,}")
        print(f"  Max allowed: {config.max_context_chars:,}")
    else:
        print("  Status: DOES NOT EXIST")

    print()

    # Credentials status
    print("Credentials:")
    config_data = load_config_yaml()

    token = config_data.get("telegram_token", "")
    token_env = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token_env:
        print("  Telegram token: set (from environment)")
    elif token and token != "YOUR_TELEGRAM_BOT_TOKEN":
        print("  Telegram token: set (from config)")
    else:
        print("  Telegram token: NOT SET")

    api_key = config_data.get("anthropic_api_key", "")
    api_key_env = os.environ.get("ANTHROPIC_API_KEY")
    if api_key_env:
        print("  Anthropic API key: set (from environment)")
    elif api_key and api_key != "YOUR_ANTHROPIC_API_KEY":
        print("  Anthropic API key: set (from config)")
    else:
        print("  Anthropic API key: NOT SET")

    print()

    # Model info
    print(f"Model: {config.model}")
    print(f"Allowed users: {config.allowed_user_ids}")

    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run the bot."""
    import logging

    from .telegram_handler import TelegramBot

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    try:
        bot_name = getattr(args, "bot", None)
        config = Config.load(bot_name=bot_name)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        print("Run 'folderbot init' to set up configuration", file=sys.stderr)
        return 1

    bot = TelegramBot(config)
    bot.run()
    return 0


# Systemd service management

SYSTEMD_SERVICE_TEMPLATE = """[Unit]
Description=Folderbot - Telegram bot for chatting with your folder
After=network.target

[Service]
Type=simple
ExecStart={exec_path} run
Restart=on-failure
RestartSec=10
WorkingDirectory={work_dir}

[Install]
WantedBy=default.target
"""


def _get_service_path() -> Path:
    """Get the path to the systemd user service file."""
    return Path.home() / ".config/systemd/user/folderbot.service"


def _run_systemctl(*args: str) -> tuple[int, str]:
    """Run a systemctl --user command."""
    import subprocess

    result = subprocess.run(
        ["systemctl", "--user", *args],
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    return result.returncode, output.strip()


def cmd_service_install(args: argparse.Namespace) -> int:
    """Install the systemd user service."""
    import shutil

    # Find the folderbot executable
    exec_path = shutil.which("folderbot")
    if not exec_path:
        print("Error: 'folderbot' not found in PATH", file=sys.stderr)
        print(
            "Make sure folderbot is installed: pip install folderbot", file=sys.stderr
        )
        return 1

    # Get config to determine working directory
    config_path = get_config_path()
    if not config_path.exists():
        print(
            "Error: No configuration found. Run 'folderbot init' first.",
            file=sys.stderr,
        )
        return 1

    config_data = load_config_yaml()
    work_dir = config_data.get("root_folder", str(Path.cwd()))

    # Create service file content
    service_content = SYSTEMD_SERVICE_TEMPLATE.format(
        exec_path=exec_path,
        work_dir=work_dir,
    )

    # Ensure directory exists
    service_path = _get_service_path()
    service_path.parent.mkdir(parents=True, exist_ok=True)

    # Write service file
    service_path.write_text(service_content)
    print(f"Service file created: {service_path}")

    # Reload systemd
    code, _ = _run_systemctl("daemon-reload")
    if code != 0:
        print("Warning: Failed to reload systemd daemon", file=sys.stderr)

    # Check if linger is enabled
    import subprocess

    linger_check = subprocess.run(
        ["loginctl", "show-user", os.environ.get("USER", ""), "--property=Linger"],
        capture_output=True,
        text=True,
    )
    linger_enabled = "Linger=yes" in linger_check.stdout

    print()
    print("Service installed. Next steps:")
    print("  folderbot service enable   # Start on login")
    print("  folderbot service start    # Start now")
    if not linger_enabled:
        print()
        print("Note: To keep the bot running after logout (recommended for servers):")
        print("  sudo loginctl enable-linger $USER")
    return 0


def cmd_service_uninstall(args: argparse.Namespace) -> int:
    """Uninstall the systemd user service."""
    service_path = _get_service_path()

    if not service_path.exists():
        print("Service is not installed.")
        return 0

    # Stop and disable first
    _run_systemctl("stop", "folderbot")
    _run_systemctl("disable", "folderbot")

    # Remove service file
    service_path.unlink()
    print(f"Service file removed: {service_path}")

    # Reload systemd
    _run_systemctl("daemon-reload")
    print("Service uninstalled.")
    return 0


def cmd_service_enable(args: argparse.Namespace) -> int:
    """Enable the service to start on login."""
    service_path = _get_service_path()
    if not service_path.exists():
        print("Error: Service not installed. Run 'folderbot service install' first.")
        return 1

    code, output = _run_systemctl("enable", "folderbot")
    if code != 0:
        print(f"Error: {output}", file=sys.stderr)
        return 1

    print("Service enabled. Folderbot will start automatically on login.")
    return 0


def cmd_service_disable(args: argparse.Namespace) -> int:
    """Disable the service from starting on login."""
    code, output = _run_systemctl("disable", "folderbot")
    if code != 0:
        print(f"Error: {output}", file=sys.stderr)
        return 1

    print("Service disabled. Folderbot will not start automatically.")
    return 0


def cmd_service_start(args: argparse.Namespace) -> int:
    """Start the service."""
    service_path = _get_service_path()
    if not service_path.exists():
        print("Error: Service not installed. Run 'folderbot service install' first.")
        return 1

    code, output = _run_systemctl("start", "folderbot")
    if code != 0:
        print(f"Error: {output}", file=sys.stderr)
        return 1

    print("Folderbot started.")
    return 0


def cmd_service_stop(args: argparse.Namespace) -> int:
    """Stop the service."""
    code, output = _run_systemctl("stop", "folderbot")
    if code != 0:
        print(f"Error: {output}", file=sys.stderr)
        return 1

    print("Folderbot stopped.")
    return 0


def cmd_service_restart(args: argparse.Namespace) -> int:
    """Restart the service."""
    service_path = _get_service_path()
    if not service_path.exists():
        print("Error: Service not installed. Run 'folderbot service install' first.")
        return 1

    code, output = _run_systemctl("restart", "folderbot")
    if code != 0:
        print(f"Error: {output}", file=sys.stderr)
        return 1

    print("Folderbot restarted.")
    return 0


def cmd_service_status(args: argparse.Namespace) -> int:
    """Show service status."""
    service_path = _get_service_path()

    if not service_path.exists():
        print("Service: not installed")
        print()
        print("Run 'folderbot service install' to set up the systemd service.")
        return 0

    code, output = _run_systemctl("status", "folderbot")
    print(output)
    return 0


def cmd_service_logs(args: argparse.Namespace) -> int:
    """Show service logs."""
    import subprocess

    cmd = [
        "journalctl",
        "--user",
        "-u",
        "folderbot",
        "-f" if args.follow else "-n",
        "50",
    ]
    if not args.follow:
        cmd = ["journalctl", "--user", "-u", "folderbot", "-n", "50"]

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass
    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="folderbot",
        description="Telegram bot for chatting with your folder using Claude AI",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run command
    run_parser = subparsers.add_parser("run", help="Start the bot")
    run_parser.add_argument(
        "--bot", "-b", help="Name of bot to run (for multi-bot configs)"
    )
    run_parser.set_defaults(func=cmd_run)

    # init command
    init_parser = subparsers.add_parser("init", help="Interactive setup wizard")
    init_parser.set_defaults(func=cmd_init)

    # status command
    status_parser = subparsers.add_parser("status", help="Show current status")
    status_parser.set_defaults(func=cmd_status)

    # config command with subcommands
    config_parser = subparsers.add_parser("config", help="View or modify configuration")
    config_subparsers = config_parser.add_subparsers(
        dest="config_command", help="Config commands"
    )

    # config show
    config_show_parser = config_subparsers.add_parser(
        "show", help="Show current configuration"
    )
    config_show_parser.set_defaults(func=cmd_config_show)

    # config set
    config_set_parser = config_subparsers.add_parser(
        "set", help="Set a configuration value"
    )
    config_set_parser.add_argument(
        "key", help="Configuration key (e.g., model, root_folder)"
    )
    config_set_parser.add_argument("value", help="Value to set")
    config_set_parser.set_defaults(func=cmd_config_set)

    # config folder (shortcut)
    config_folder_parser = config_subparsers.add_parser(
        "folder", help="Set the root folder"
    )
    config_folder_parser.add_argument("path", help="Path to the folder")
    config_folder_parser.set_defaults(func=cmd_config_folder)

    # service command with subcommands
    service_parser = subparsers.add_parser(
        "service", help="Manage systemd user service"
    )
    service_subparsers = service_parser.add_subparsers(
        dest="service_command", help="Service commands"
    )

    # service install
    service_install_parser = service_subparsers.add_parser(
        "install", help="Install systemd user service"
    )
    service_install_parser.set_defaults(func=cmd_service_install)

    # service uninstall
    service_uninstall_parser = service_subparsers.add_parser(
        "uninstall", help="Uninstall systemd user service"
    )
    service_uninstall_parser.set_defaults(func=cmd_service_uninstall)

    # service enable
    service_enable_parser = service_subparsers.add_parser(
        "enable", help="Enable service to start on login"
    )
    service_enable_parser.set_defaults(func=cmd_service_enable)

    # service disable
    service_disable_parser = service_subparsers.add_parser(
        "disable", help="Disable service auto-start"
    )
    service_disable_parser.set_defaults(func=cmd_service_disable)

    # service start
    service_start_parser = service_subparsers.add_parser(
        "start", help="Start the service"
    )
    service_start_parser.set_defaults(func=cmd_service_start)

    # service stop
    service_stop_parser = service_subparsers.add_parser("stop", help="Stop the service")
    service_stop_parser.set_defaults(func=cmd_service_stop)

    # service restart
    service_restart_parser = service_subparsers.add_parser(
        "restart", help="Restart the service"
    )
    service_restart_parser.set_defaults(func=cmd_service_restart)

    # service status
    service_status_parser = service_subparsers.add_parser(
        "status", help="Show service status"
    )
    service_status_parser.set_defaults(func=cmd_service_status)

    # service logs
    service_logs_parser = service_subparsers.add_parser(
        "logs", help="Show service logs"
    )
    service_logs_parser.add_argument(
        "-f", "--follow", action="store_true", help="Follow log output"
    )
    service_logs_parser.set_defaults(func=cmd_service_logs)

    return parser


def main() -> int:
    """Main entry point."""
    try:
        parser = create_parser()
        args = parser.parse_args()

        if args.command is None:
            # Default: show help
            parser.print_help()
            return 0

        if args.command == "config" and getattr(args, "config_command", None) is None:
            # config without subcommand: show config
            return cmd_config_show(args)

        if args.command == "service" and getattr(args, "service_command", None) is None:
            # service without subcommand: show status
            return cmd_service_status(args)

        if hasattr(args, "func"):
            return args.func(args)

        parser.print_help()
        return 0
    except KeyboardInterrupt:
        print("\n\nAborted.")
        return 130

"""Helper utilities for custom tools."""

from pathlib import Path

from dotenv import dotenv_values


def load_env(root_folder: Path, filename: str = ".env") -> dict[str, str | None]:
    """Load environment variables from a .env file in the root folder.

    Args:
        root_folder: The root folder path
        filename: Name of the env file (default: .env)

    Returns:
        Dictionary of environment variables

    Example:
        ```python
        from folderbot.tools.helpers import load_env

        class CustomTools:
            def __init__(self, root_folder: Path):
                self.root_folder = root_folder
                self.env = load_env(root_folder)
                self.api_key = self.env.get("MY_API_KEY")
        ```
    """
    env_path = root_folder / filename
    if not env_path.exists():
        return {}
    return dotenv_values(env_path)

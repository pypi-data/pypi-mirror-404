"""Custom tools loader for user-defined tools."""

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Protocol

from .base import ToolResult

logger = logging.getLogger(__name__)


class CustomToolsProtocol(Protocol):
    """Protocol that custom tools must implement."""

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Return tool definitions for the Claude API."""
        ...

    def execute(self, tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        """Execute a tool and return the result."""
        ...


def load_custom_tools(root_folder: Path) -> CustomToolsProtocol | None:
    """Load custom tools from .folderbot/tools.py or .folderbot/tools/__init__.py.

    The custom tools module should export either:
    1. A `CustomTools` class that implements get_tool_definitions() and execute()
    2. A `create_tools(root_folder: Path)` function that returns such an object

    Args:
        root_folder: The root folder to look for .folderbot/tools in

    Returns:
        A custom tools object, or None if no custom tools found
    """
    folderbot_dir = root_folder / ".folderbot"

    # Check for .folderbot/tools.py
    tools_file = folderbot_dir / "tools.py"
    if tools_file.exists():
        return _load_module(tools_file, root_folder)

    # Check for .folderbot/tools/__init__.py
    tools_package = folderbot_dir / "tools" / "__init__.py"
    if tools_package.exists():
        return _load_module(tools_package, root_folder, is_package=True)

    return None


def _load_module(
    module_path: Path, root_folder: Path, is_package: bool = False
) -> CustomToolsProtocol | None:
    """Load a Python module from a file path.

    Args:
        module_path: Path to the .py file
        root_folder: Root folder to pass to create_tools()
        is_package: Whether this is a package (__init__.py)

    Returns:
        A custom tools object, or None if loading failed
    """
    try:
        # Create a unique module name to avoid conflicts
        module_name = f"folderbot_custom_tools_{id(module_path)}"

        spec = importlib.util.spec_from_file_location(
            module_name,
            module_path,
            submodule_search_locations=[str(module_path.parent)]
            if is_package
            else None,
        )

        if spec is None or spec.loader is None:
            logger.warning(f"Could not load module spec from {module_path}")
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        # Add the .folderbot directory to path so imports work
        folderbot_dir = str(
            module_path.parent.parent if is_package else module_path.parent
        )
        if folderbot_dir not in sys.path:
            sys.path.insert(0, folderbot_dir)

        try:
            spec.loader.exec_module(module)
        finally:
            # Clean up sys.path
            if folderbot_dir in sys.path:
                sys.path.remove(folderbot_dir)

        # Try to get custom tools object
        # Option 1: create_tools(root_folder) function
        if hasattr(module, "create_tools"):
            tools = module.create_tools(root_folder)
            logger.info(f"Loaded custom tools from {module_path} via create_tools()")
            return tools

        # Option 2: CustomTools class
        if hasattr(module, "CustomTools"):
            tools = module.CustomTools(root_folder)
            logger.info(f"Loaded custom tools from {module_path} via CustomTools class")
            return tools

        logger.warning(
            f"Custom tools module {module_path} found but no CustomTools class "
            "or create_tools() function defined"
        )
        return None

    except Exception as e:
        logger.exception(f"Error loading custom tools from {module_path}: {e}")
        return None

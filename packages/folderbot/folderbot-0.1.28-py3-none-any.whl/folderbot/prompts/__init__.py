"""Prompt loading utilities for folderbot."""

from pathlib import Path

# Directory containing prompt files
PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt from a .txt file.

    Args:
        name: The name of the prompt file (without .txt extension)

    Returns:
        The prompt text content

    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    prompt_file = PROMPTS_DIR / f"{name}.txt"
    return prompt_file.read_text(encoding="utf-8")


# Pre-load commonly used prompts for convenience
def get_system_prompt() -> str:
    """Get the main system prompt template."""
    return load_prompt("system")


def get_action_validator_prompt() -> str:
    """Get the action validator prompt."""
    return load_prompt("action_validator")


def get_tool_retry_correction_prompt() -> str:
    """Get the tool retry correction prompt."""
    return load_prompt("tool_retry_correction")


def get_task_summary_prompt() -> str:
    """Get the task summary prompt template."""
    return load_prompt("task_summary")

"""List files tool."""

from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class ListFilesInput:
    """Input for listing files in a directory."""

    path: str = Field(
        default="",
        description=(
            "Subfolder path relative to root (e.g., 'notes/2024'). "
            "Empty string or omit for root folder."
        ),
    )
    pattern: str = Field(
        default="*",
        description="Glob pattern to filter files (e.g., '*.md'). Defaults to all files.",
    )

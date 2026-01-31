"""Read multiple files tool."""

from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class ReadFilesInput:
    """Input for reading multiple files."""

    paths: list[str] = Field(
        description=(
            "List of file paths relative to the root folder "
            "(e.g., ['notes/todo.md', 'notes/ideas.md'])"
        )
    )

"""Read file tool."""

from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class ReadFileInput:
    """Input for reading a file."""

    path: str = Field(
        description="File path relative to the root folder (e.g., 'notes/todo.md')"
    )

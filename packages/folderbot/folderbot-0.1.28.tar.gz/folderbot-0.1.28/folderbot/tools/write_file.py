"""Write file tool."""

from enum import Enum

from pydantic import Field
from pydantic.dataclasses import dataclass


class WriteMode(str, Enum):
    """Write mode for file operations."""

    overwrite = "overwrite"
    append = "append"


@dataclass(frozen=True)
class WriteFileInput:
    """Input for writing a file."""

    path: str = Field(
        description="File path relative to the root folder (e.g., 'notes/todo.md')"
    )
    content: str = Field(description="Content to write to the file")
    mode: WriteMode = Field(
        default=WriteMode.overwrite,
        description="Write mode: 'overwrite' replaces file content, 'append' adds to end.",
    )

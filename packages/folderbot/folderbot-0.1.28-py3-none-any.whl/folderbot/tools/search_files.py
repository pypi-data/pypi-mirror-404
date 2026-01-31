"""Search files tool."""

from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class SearchFilesInput:
    """Input for searching files."""

    query: str = Field(description="Text to search for (case-insensitive)")
    max_results: int = Field(
        default=10, description="Maximum number of matching files to return."
    )

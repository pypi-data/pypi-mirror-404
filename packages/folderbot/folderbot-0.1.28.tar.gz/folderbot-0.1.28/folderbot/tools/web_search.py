"""Web search tool."""

from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class WebSearchInput:
    """Input for searching the web."""

    query: str = Field(description="Search query to look up on the web")
    max_results: int = Field(
        default=5,
        description="Maximum number of search results to return (1-10)",
    )

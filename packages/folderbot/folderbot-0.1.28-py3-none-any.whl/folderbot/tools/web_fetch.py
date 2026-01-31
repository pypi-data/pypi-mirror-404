"""Web fetch tool."""

from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class WebFetchInput:
    """Input for fetching content from a URL."""

    url: str = Field(description="URL to fetch content from")
    max_chars: int = Field(
        default=10000,
        description="Maximum characters to return from the page content",
    )

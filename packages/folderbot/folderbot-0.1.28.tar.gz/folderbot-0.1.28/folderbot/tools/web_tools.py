"""Web tools for searching and fetching content from the web."""

import logging
from typing import Any

from .base import ToolDefinition, ToolResult
from .web_fetch import WebFetchInput
from .web_search import WebSearchInput

logger = logging.getLogger(__name__)

# Check if web dependencies are available
_WEB_AVAILABLE = False
try:
    from duckduckgo_search import DDGS

    _WEB_AVAILABLE = True
except ImportError:
    DDGS = None  # type: ignore[assignment, misc]

_FETCH_AVAILABLE = False
try:
    import httpx
    from bs4 import BeautifulSoup

    _FETCH_AVAILABLE = True
except ImportError:
    httpx = None  # type: ignore[assignment]
    BeautifulSoup = None  # type: ignore[assignment, misc]


WEB_TOOL_DEFINITIONS = [
    ToolDefinition(
        name="web_search",
        description=(
            "Search the web using DuckDuckGo. Returns titles, URLs, and snippets "
            "for the top results. Use this to find information online."
        ),
        input_model=WebSearchInput,
    ),
    ToolDefinition(
        name="web_fetch",
        description=(
            "Fetch and extract text content from a URL. Returns the main text "
            "content of the page, stripping HTML. Use this to read articles, "
            "documentation, or other web pages."
        ),
        input_model=WebFetchInput,
    ),
]


class WebTools:
    """Tools for web search and content fetching."""

    def __init__(self) -> None:
        self._search_available = _WEB_AVAILABLE
        self._fetch_available = _FETCH_AVAILABLE

    def is_available(self) -> bool:
        """Check if any web tools are available."""
        return self._search_available or self._fetch_available

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions for available web tools."""
        definitions = []
        if self._search_available:
            definitions.append(WEB_TOOL_DEFINITIONS[0].to_api_format())
        if self._fetch_available:
            definitions.append(WEB_TOOL_DEFINITIONS[1].to_api_format())
        return definitions

    def execute(self, tool_name: str, tool_input: dict[str, Any]) -> ToolResult | None:
        """Execute a web tool. Returns None if tool not found."""
        handlers = {
            "web_search": self._web_search,
            "web_fetch": self._web_fetch,
        }

        handler = handlers.get(tool_name)
        if handler:
            return handler(tool_input)
        return None

    def _web_search(self, tool_input: dict[str, Any]) -> ToolResult:
        """Search the web using DuckDuckGo."""
        if not self._search_available:
            return ToolResult(
                content="Web search not available. Install with: pip install folderbot[web]",
                is_error=True,
            )

        params = WebSearchInput(**tool_input)
        max_results = min(max(1, params.max_results), 10)

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(params.query, max_results=max_results))

            if not results:
                return ToolResult(content=f"No results found for: {params.query}")

            lines = []
            for i, r in enumerate(results, 1):
                title = r.get("title", "No title")
                url = r.get("href", r.get("link", ""))
                snippet = r.get("body", r.get("snippet", ""))
                lines.append(f"{i}. {title}\n   {url}\n   {snippet}\n")

            return ToolResult(content="\n".join(lines))

        except Exception as e:
            logger.exception("Web search error")
            return ToolResult(content=f"Search error: {e}", is_error=True)

    def _web_fetch(self, tool_input: dict[str, Any]) -> ToolResult:
        """Fetch and extract content from a URL."""
        if not self._fetch_available:
            return ToolResult(
                content="Web fetch not available. Install with: pip install folderbot[web]",
                is_error=True,
            )

        params = WebFetchInput(**tool_input)

        try:
            # Fetch the URL
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (compatible; Folderbot/1.0; "
                    "+https://gitlab.com/jorgeecardona/folderbot)"
                )
            }
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(params.url, headers=headers)
                response.raise_for_status()

            content_type = response.headers.get("content-type", "")

            # Handle plain text
            if "text/plain" in content_type:
                text = response.text[: params.max_chars]
                if len(response.text) > params.max_chars:
                    text += f"\n\n[Truncated at {params.max_chars} characters]"
                return ToolResult(content=text)

            # Handle HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # Get text content
            text = soup.get_text(separator="\n", strip=True)

            # Clean up multiple newlines
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            text = "\n".join(lines)

            # Truncate if needed
            if len(text) > params.max_chars:
                text = (
                    text[: params.max_chars]
                    + f"\n\n[Truncated at {params.max_chars} characters]"
                )

            # Get title if available
            title = soup.title.string if soup.title else None
            if title:
                text = f"Title: {title}\n\n{text}"

            return ToolResult(content=text)

        except httpx.HTTPStatusError as e:
            return ToolResult(
                content=f"HTTP error {e.response.status_code}: {params.url}",
                is_error=True,
            )
        except Exception as e:
            logger.exception("Web fetch error")
            return ToolResult(content=f"Fetch error: {e}", is_error=True)

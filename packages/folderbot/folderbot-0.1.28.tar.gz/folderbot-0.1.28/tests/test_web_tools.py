"""Tests for web tools."""

from unittest.mock import MagicMock, patch

from folderbot.tools.web_fetch import WebFetchInput
from folderbot.tools.web_search import WebSearchInput
from folderbot.tools.web_tools import WebTools


class TestWebSearchInput:
    """Tests for WebSearchInput dataclass."""

    def test_defaults(self):
        """Test default values."""
        input_model = WebSearchInput(query="test")
        assert input_model.query == "test"
        assert input_model.max_results == 5

    def test_custom_max_results(self):
        """Test custom max_results."""
        input_model = WebSearchInput(query="test", max_results=10)
        assert input_model.max_results == 10


class TestWebFetchInput:
    """Tests for WebFetchInput dataclass."""

    def test_defaults(self):
        """Test default values."""
        input_model = WebFetchInput(url="https://example.com")
        assert input_model.url == "https://example.com"
        assert input_model.max_chars == 10000

    def test_custom_max_chars(self):
        """Test custom max_chars."""
        input_model = WebFetchInput(url="https://example.com", max_chars=5000)
        assert input_model.max_chars == 5000


class TestWebTools:
    """Tests for WebTools class."""

    def test_init(self):
        """Test WebTools initialization."""
        tools = WebTools()
        # Should not raise, even if dependencies are missing
        assert isinstance(tools, WebTools)

    def test_execute_unknown_tool(self):
        """Test execute returns None for unknown tools."""
        tools = WebTools()
        result = tools.execute("unknown_tool", {})
        assert result is None

    def test_get_tool_definitions_structure(self):
        """Test tool definitions have correct structure."""
        tools = WebTools()
        definitions = tools.get_tool_definitions()
        # May be empty if dependencies not installed
        for defn in definitions:
            assert "name" in defn
            assert "description" in defn
            assert "input_schema" in defn


class TestWebSearchExecution:
    """Tests for web_search tool execution."""

    @patch("folderbot.tools.web_tools._WEB_AVAILABLE", False)
    def test_search_unavailable(self):
        """Test search when dependencies not available."""
        tools = WebTools()
        tools._search_available = False
        result = tools._web_search({"query": "test"})
        assert result.is_error
        assert "not available" in result.content

    @patch("folderbot.tools.web_tools._WEB_AVAILABLE", True)
    @patch("folderbot.tools.web_tools.DDGS")
    def test_search_success(self, mock_ddgs_class):
        """Test successful search."""
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [
            {"title": "Result 1", "href": "https://example.com/1", "body": "Snippet 1"},
            {"title": "Result 2", "href": "https://example.com/2", "body": "Snippet 2"},
        ]
        mock_ddgs_class.return_value = mock_ddgs

        tools = WebTools()
        tools._search_available = True
        result = tools._web_search({"query": "python programming"})

        assert not result.is_error
        assert "Result 1" in result.content
        assert "Result 2" in result.content
        assert "https://example.com/1" in result.content

    @patch("folderbot.tools.web_tools._WEB_AVAILABLE", True)
    @patch("folderbot.tools.web_tools.DDGS")
    def test_search_no_results(self, mock_ddgs_class):
        """Test search with no results."""
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = []
        mock_ddgs_class.return_value = mock_ddgs

        tools = WebTools()
        tools._search_available = True
        result = tools._web_search({"query": "xyznonexistent123"})

        assert not result.is_error
        assert "No results found" in result.content

    @patch("folderbot.tools.web_tools._WEB_AVAILABLE", True)
    @patch("folderbot.tools.web_tools.DDGS")
    def test_search_max_results_clamped(self, mock_ddgs_class):
        """Test max_results is clamped to 1-10."""
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = []
        mock_ddgs_class.return_value = mock_ddgs

        tools = WebTools()
        tools._search_available = True

        # Test max_results > 10 gets clamped
        tools._web_search({"query": "test", "max_results": 100})
        mock_ddgs.text.assert_called_with("test", max_results=10)

        # Test max_results < 1 gets clamped
        tools._web_search({"query": "test", "max_results": 0})
        mock_ddgs.text.assert_called_with("test", max_results=1)


class TestWebFetchExecution:
    """Tests for web_fetch tool execution."""

    @patch("folderbot.tools.web_tools._FETCH_AVAILABLE", False)
    def test_fetch_unavailable(self):
        """Test fetch when dependencies not available."""
        tools = WebTools()
        tools._fetch_available = False
        result = tools._web_fetch({"url": "https://example.com"})
        assert result.is_error
        assert "not available" in result.content

    @patch("folderbot.tools.web_tools._FETCH_AVAILABLE", True)
    @patch("folderbot.tools.web_tools.httpx")
    @patch("folderbot.tools.web_tools.BeautifulSoup")
    def test_fetch_html_success(self, mock_bs, mock_httpx):
        """Test successful HTML fetch."""
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "<html><body><p>Hello World</p></body></html>"
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        mock_soup = MagicMock()
        mock_soup.title = MagicMock()
        mock_soup.title.string = "Test Page"
        mock_soup.get_text.return_value = "Hello World"
        mock_soup.return_value = mock_soup
        mock_bs.return_value = mock_soup

        tools = WebTools()
        tools._fetch_available = True
        result = tools._web_fetch({"url": "https://example.com"})

        assert not result.is_error
        assert "Hello World" in result.content

    @patch("folderbot.tools.web_tools._FETCH_AVAILABLE", True)
    @patch("folderbot.tools.web_tools.httpx")
    def test_fetch_plain_text(self, mock_httpx):
        """Test fetching plain text content."""
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "Plain text content"
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        tools = WebTools()
        tools._fetch_available = True
        result = tools._web_fetch({"url": "https://example.com/file.txt"})

        assert not result.is_error
        assert "Plain text content" in result.content

    @patch("folderbot.tools.web_tools._FETCH_AVAILABLE", True)
    @patch("folderbot.tools.web_tools.httpx")
    def test_fetch_truncation(self, mock_httpx):
        """Test content truncation at max_chars."""
        long_content = "x" * 20000
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = long_content
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        tools = WebTools()
        tools._fetch_available = True
        result = tools._web_fetch({"url": "https://example.com", "max_chars": 1000})

        assert not result.is_error
        assert len(result.content) < 1200  # Some buffer for truncation message
        assert "Truncated" in result.content

"""Base classes for tools."""

from dataclasses import dataclass
from typing import Any

from pydantic import TypeAdapter


@dataclass(frozen=True)
class ToolResult:
    """Result of a tool execution."""

    content: str
    is_error: bool = False


@dataclass(frozen=True)
class ToolDefinition:
    """A tool definition with its input model."""

    name: str
    description: str
    input_model: type
    requires_confirmation: bool = False  # If True, Claude should ask before using

    def to_api_format(self) -> dict[str, Any]:
        """Convert to Anthropic API tool format."""
        schema = TypeAdapter(self.input_model).json_schema()
        # Remove title and description from top level (Anthropic uses our description)
        schema.pop("title", None)
        schema.pop("description", None)
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": schema,
        }

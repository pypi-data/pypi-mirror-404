"""Utility tools for common operations."""

import random
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import Field
from pydantic.dataclasses import dataclass

from .base import ToolDefinition, ToolResult


@dataclass(frozen=True)
class GetTimeInput:
    """Input for getting current time."""

    timezone: str = Field(
        default="UTC",
        description="Timezone (e.g., 'UTC', 'America/New_York', 'Europe/London')",
    )
    format: str = Field(
        default="%Y-%m-%d %H:%M:%S",
        description="strftime format string",
    )


@dataclass(frozen=True)
class CompareNumbersInput:
    """Input for comparing two numbers."""

    a: float = Field(description="First number")
    b: float = Field(description="Second number")


@dataclass(frozen=True)
class ShuffleListInput:
    """Input for shuffling a list."""

    items: list[str] = Field(description="List of items to shuffle")


@dataclass(frozen=True)
class SortListInput:
    """Input for sorting a list."""

    items: list[str | float] = Field(description="List of items to sort")
    reverse: bool = Field(default=False, description="Sort in descending order")
    numeric: bool = Field(
        default=False, description="Treat items as numbers for sorting"
    )


@dataclass(frozen=True)
class RandomChoiceInput:
    """Input for picking random items."""

    items: list[str] = Field(description="List of items to choose from")
    count: int = Field(
        default=1, description="Number of items to pick (without replacement)"
    )


@dataclass(frozen=True)
class RandomNumberInput:
    """Input for generating a random number."""

    min: float = Field(default=0, description="Minimum value (inclusive)")
    max: float = Field(default=100, description="Maximum value (inclusive)")
    integer: bool = Field(default=True, description="Return an integer")


@dataclass(frozen=True)
class SendMessageInput:
    """Input for sending a message to the user."""

    message: str = Field(description="The message text to send to the user")


UTIL_TOOL_DEFINITIONS = [
    ToolDefinition(
        name="get_time",
        description="Get the current date and time. Useful for knowing what day/time it is.",
        input_model=GetTimeInput,
    ),
    ToolDefinition(
        name="compare_numbers",
        description="Compare two numbers. Returns which is greater, lesser, or if equal.",
        input_model=CompareNumbersInput,
    ),
    ToolDefinition(
        name="shuffle_list",
        description="Randomly shuffle a list of items.",
        input_model=ShuffleListInput,
    ),
    ToolDefinition(
        name="sort_list",
        description="Sort a list of items alphabetically or numerically.",
        input_model=SortListInput,
    ),
    ToolDefinition(
        name="random_choice",
        description="Pick random item(s) from a list.",
        input_model=RandomChoiceInput,
    ),
    ToolDefinition(
        name="random_number",
        description="Generate a random number within a range.",
        input_model=RandomNumberInput,
    ),
    ToolDefinition(
        name="send_message",
        description=(
            "Send a message directly to the user via Telegram. "
            "Use this in scheduled tasks to send notifications, greetings, "
            "reminders, or any other message to the user."
        ),
        input_model=SendMessageInput,
    ),
]


class UtilTools:
    """Utility tools for common operations."""

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions for the API."""
        return [t.to_api_format() for t in UTIL_TOOL_DEFINITIONS]

    def execute(self, tool_name: str, tool_input: dict[str, Any]) -> ToolResult | None:
        """Execute a utility tool. Returns None if tool not found."""
        handlers = {
            "get_time": self._get_time,
            "compare_numbers": self._compare_numbers,
            "shuffle_list": self._shuffle_list,
            "sort_list": self._sort_list,
            "random_choice": self._random_choice,
            "random_number": self._random_number,
            "send_message": self._send_message,
        }

        handler = handlers.get(tool_name)
        if handler:
            return handler(tool_input)
        return None

    def _get_time(self, tool_input: dict[str, Any]) -> ToolResult:
        params = GetTimeInput(**tool_input)
        try:
            tz = ZoneInfo(params.timezone)
            now = datetime.now(tz)
            formatted = now.strftime(params.format)
            return ToolResult(content=f"{formatted} ({params.timezone})")
        except Exception as e:
            return ToolResult(content=f"Error: {e}", is_error=True)

    def _compare_numbers(self, tool_input: dict[str, Any]) -> ToolResult:
        params = CompareNumbersInput(**tool_input)
        if params.a > params.b:
            result = f"{params.a} > {params.b} (a is greater)"
        elif params.a < params.b:
            result = f"{params.a} < {params.b} (b is greater)"
        else:
            result = f"{params.a} = {params.b} (equal)"
        return ToolResult(content=result)

    def _shuffle_list(self, tool_input: dict[str, Any]) -> ToolResult:
        params = ShuffleListInput(**tool_input)
        items = list(params.items)
        random.shuffle(items)
        return ToolResult(content="\n".join(items))

    def _sort_list(self, tool_input: dict[str, Any]) -> ToolResult:
        params = SortListInput(**tool_input)

        if params.numeric:
            try:
                sorted_nums = sorted(
                    [float(x) for x in params.items], reverse=params.reverse
                )
                sorted_items = [
                    str(int(x)) if x == int(x) else str(x) for x in sorted_nums
                ]
            except ValueError as e:
                return ToolResult(
                    content=f"Error converting to numbers: {e}", is_error=True
                )
        else:
            sorted_items = sorted(
                [str(x) for x in params.items], reverse=params.reverse
            )

        return ToolResult(content="\n".join(sorted_items))

    def _random_choice(self, tool_input: dict[str, Any]) -> ToolResult:
        params = RandomChoiceInput(**tool_input)
        if params.count > len(params.items):
            return ToolResult(
                content=f"Cannot pick {params.count} items from list of {len(params.items)}",
                is_error=True,
            )
        if params.count == 1:
            return ToolResult(content=random.choice(params.items))
        choices = random.sample(list(params.items), params.count)
        return ToolResult(content="\n".join(choices))

    def _random_number(self, tool_input: dict[str, Any]) -> ToolResult:
        params = RandomNumberInput(**tool_input)
        if params.integer:
            result: int | float = random.randint(int(params.min), int(params.max))
        else:
            result = random.uniform(params.min, params.max)
        return ToolResult(content=str(result))

    def _send_message(self, tool_input: dict[str, Any]) -> ToolResult:
        params = SendMessageInput(**tool_input)
        return ToolResult(content=params.message)

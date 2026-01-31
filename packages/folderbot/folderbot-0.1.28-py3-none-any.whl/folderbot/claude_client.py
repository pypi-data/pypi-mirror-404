"""Claude API client wrapper with tool use support."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from anthropic import AsyncAnthropic

from .config import Config
from .prompts import (
    get_action_validator_prompt,
    get_system_prompt,
    get_tool_retry_correction_prompt,
)
from .session_manager import Message
from .tools import FolderTools

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .scheduler.tools import SchedulerTools


class ClaudeClient:
    """Wrapper for Claude API interactions with tool support."""

    MAX_TOOL_ITERATIONS = 10  # Prevent infinite loops
    MAX_VALIDATION_RETRIES = 2  # Max retries when response validation fails

    def __init__(
        self,
        config: Config,
        scheduler_tools: SchedulerTools | None = None,
    ):
        self.config = config
        self.client = AsyncAnthropic(api_key=config.anthropic_api_key)
        self.tools = FolderTools(config, scheduler_tools=scheduler_tools)

    def _build_system_prompt(self) -> str:
        """Build system prompt with dynamic tool confirmation section."""
        confirmation_tools = self.tools.get_tools_requiring_confirmation()

        if confirmation_tools:
            tools_list = ", ".join(confirmation_tools)
            confirmation_section = (
                f"- EXCEPTION: Ask for confirmation before using: {tools_list}\n"
            )
        else:
            confirmation_section = ""

        return get_system_prompt().format(
            user_name=self.config.user_name,
            confirmation_tools_section=confirmation_section,
        )

    async def chat(
        self,
        user_message: str,
        context: str,
        history: list[Message],
        on_tool_use: Callable[[str], Awaitable[None]] | None = None,
        chat_id: int = 0,
        user_id: int = 0,
    ) -> tuple[str, list[str]]:
        """Send a message to Claude and get a response.

        Args:
            user_message: The user's message
            context: Legacy parameter, now unused (kept for backward compatibility)
            history: Conversation history
            on_tool_use: Optional async callback called when tools are being used.
                         Receives the tool name as argument. Useful for progress updates.
            chat_id: Telegram chat ID (for scheduler tools)
            user_id: Telegram user ID (for scheduler tools)

        Returns:
            Tuple of (Claude's text response, list of tools used)
        """
        system = self._build_system_prompt()

        # Build messages list from history
        messages: list[dict[str, Any]] = []
        for msg in history:
            messages.append(
                {
                    "role": msg["role"],
                    "content": msg["content"],
                }
            )

        # Add the new user message
        messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        # Get tool definitions
        tool_definitions = self.tools.get_tool_definitions()

        # Track tools used (deterministic, for appending to response)
        tools_used: list[str] = []

        # Agentic loop
        response = None
        for _ in range(self.MAX_TOOL_ITERATIONS):
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=4096,
                system=system,
                messages=messages,  # type: ignore[arg-type]
                tools=tool_definitions,  # type: ignore[arg-type]
            )

            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Process tool use blocks
                tool_results: list[dict[str, Any]] = []

                for block in response.content:
                    if block.type == "tool_use":
                        # Track tool usage (deterministic)
                        tools_used.append(block.name)
                        # Notify caller that we're using a tool
                        if on_tool_use:
                            await on_tool_use(block.name)
                        result = await self.tools.execute_async(  # type: ignore[arg-type]
                            block.name,
                            block.input,
                            chat_id=chat_id,
                            user_id=user_id,
                        )
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result.content,
                                "is_error": result.is_error,
                            }
                        )

                # Add assistant response and tool results to messages
                messages.append(
                    {
                        "role": "assistant",
                        "content": response.content,  # type: ignore[arg-type]
                    }
                )
                messages.append(
                    {
                        "role": "user",
                        "content": tool_results,
                    }
                )

            else:
                # No more tool use - done
                break

        # Extract text from final response
        if response is None:
            return "", tools_used

        text_parts: list[str] = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)

        final_response = "\n".join(text_parts) if text_parts else ""

        # If tools were used but response is empty, ask Claude to summarize
        if tools_used and not final_response.strip():
            logger.warning("Empty response after tool use, requesting summary")
            final_response = await self._request_summary_after_tools(
                messages=messages,
                system=system,
            )

        # Validate response if no tools were used but response might claim actions
        if not tools_used and final_response:
            is_valid = await self._validate_response(final_response)
            if not is_valid:
                logger.warning(
                    "Response validation failed - claims action without tool use, "
                    "retrying with stronger prompt"
                )
                # Retry with a stronger prompt reminding to use tools
                retry_response, retry_tools = await self._retry_with_tool_reminder(
                    user_message=user_message,
                    original_response=final_response,
                    history=history,
                    on_tool_use=on_tool_use,
                    chat_id=chat_id,
                    user_id=user_id,
                )
                return retry_response, retry_tools

        return final_response, tools_used

    async def _retry_with_tool_reminder(
        self,
        user_message: str,
        original_response: str,
        history: list[Message],
        on_tool_use: Callable[[str], Awaitable[None]] | None = None,
        chat_id: int = 0,
        user_id: int = 0,
    ) -> tuple[str, list[str]]:
        """Retry a request when the original response claimed actions without tools.

        Adds context about the failed response and strongly reminds to use tools.
        """
        system = self._build_system_prompt()

        # Build messages list from history
        messages: list[dict[str, Any]] = []
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add the original user message
        messages.append({"role": "user", "content": user_message})

        # Add the hallucinated response
        messages.append({"role": "assistant", "content": original_response})

        # Add correction prompt
        correction_prompt = get_tool_retry_correction_prompt()
        messages.append({"role": "user", "content": correction_prompt})

        # Get tool definitions
        tool_definitions = self.tools.get_tool_definitions()
        tools_used: list[str] = []

        # Run the agentic loop again
        response = None
        for _ in range(self.MAX_TOOL_ITERATIONS):
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=4096,
                system=system,
                messages=messages,  # type: ignore[arg-type]
                tools=tool_definitions,  # type: ignore[arg-type]
            )

            if response.stop_reason == "tool_use":
                tool_results: list[dict[str, Any]] = []

                for block in response.content:
                    if block.type == "tool_use":
                        tools_used.append(block.name)
                        if on_tool_use:
                            await on_tool_use(block.name)
                        result = await self.tools.execute_async(  # type: ignore[arg-type]
                            block.name,
                            block.input,
                            chat_id=chat_id,
                            user_id=user_id,
                        )
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result.content,
                                "is_error": result.is_error,
                            }
                        )

                messages.append(
                    {"role": "assistant", "content": response.content}  # type: ignore[arg-type]
                )
                messages.append({"role": "user", "content": tool_results})
            else:
                break

        if response is None:
            return "", tools_used

        text_parts: list[str] = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)

        final_response = "\n".join(text_parts) if text_parts else ""

        # If still no tools used after retry, log but don't loop forever
        if not tools_used and final_response:
            is_valid = await self._validate_response(final_response)
            if not is_valid:
                logger.error(
                    "Response validation failed again after retry - "
                    "model may not have access to required tool"
                )

        return final_response, tools_used

    async def _request_summary_after_tools(
        self,
        messages: list[dict[str, Any]],
        system: str,
    ) -> str:
        """Request a summary when Claude used tools but gave no text response.

        This happens when Claude's final response contains only tool_use blocks
        without any text content.
        """
        # Add a prompt asking for a summary that flows naturally for the user
        messages_with_prompt = messages.copy()
        messages_with_prompt.append(
            {
                "role": "user",
                "content": (
                    "[SYSTEM: Your previous response only contained tool calls without "
                    "any text for the user. Please provide a response that directly "
                    "answers the user's original question based on the tool results. "
                    "Do NOT acknowledge this system message or apologize - just respond "
                    "naturally as if continuing the conversation with the user.]"
                ),
            }
        )

        try:
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=1024,
                system=system,
                messages=messages_with_prompt,  # type: ignore[arg-type]
            )

            text_parts: list[str] = []
            for block in response.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)

            return "\n".join(text_parts) if text_parts else "(No response)"

        except Exception as e:
            logger.error(f"Failed to get summary after tools: {e}")
            return "(Tool executed but no summary available)"

    async def _validate_response(
        self,
        response_text: str,
    ) -> bool:
        """Validate that a response doesn't claim actions without tool use.

        Uses a fast, cheap Claude call to judge if the response claims to have
        performed actions that would require tool use.

        Args:
            response_text: The assistant's response to validate

        Returns:
            True if response is valid (doesn't falsely claim actions), False otherwise
        """
        try:
            validation_response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",  # Fast, cheap model for validation
                max_tokens=20,
                system=get_action_validator_prompt(),
                messages=[
                    {
                        "role": "user",
                        "content": f"Assistant response to validate:\n\n{response_text}",
                    }
                ],
            )

            # Extract the validation result
            result_text = ""
            for block in validation_response.content:
                if hasattr(block, "text"):
                    result_text += block.text

            result = result_text.strip().upper()
            logger.debug(f"Response validation result: {result}")

            # If the response claims an action but no tools were used, it's invalid
            if "CLAIMS_ACTION" in result:
                return False

            return True

        except Exception as e:
            # On validation error, let the response through (fail open)
            logger.warning(f"Response validation failed with error: {e}")
            return True

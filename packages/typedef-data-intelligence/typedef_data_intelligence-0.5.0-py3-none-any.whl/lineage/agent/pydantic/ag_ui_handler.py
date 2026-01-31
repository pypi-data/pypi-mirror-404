"""Custom AG-UI handler with thinking block support.

This module wraps PydanticAI's handle_ag_ui_request to capture extended thinking
blocks from Claude's reasoning process and store them in state for frontend rendering.
State updates are automatically emitted via AG-UI protocol state_update events.
"""

import json
import logging
from datetime import datetime, timezone
from typing import AsyncIterator

from fastapi import Request
from fastapi.responses import StreamingResponse
from pydantic_ai import Agent
from pydantic_ai.ag_ui import OnCompleteFunc
from pydantic_ai.ag_ui import handle_ag_ui_request as _handle_ag_ui_request
from pydantic_ai.messages import ModelResponse, ThinkingPart

from .types import AgentState, ThinkingBlock

logger = logging.getLogger(__name__)
MAX_ERROR_MESSAGE_LENGTH = 300


async def handle_ag_ui_request_with_thinking(
    agent: Agent,
    request: Request,
    deps: any,
    on_complete: OnCompleteFunc | None = None,
) -> StreamingResponse:
    """Custom AG-UI handler that captures thinking blocks.

    This wraps PydanticAI's standard handler to:
    1. Extract thinking blocks from conversation history after run
    2. Store thinking in deps.state.thinking_blocks
    3. State updates are automatically emitted via AG-UI protocol

    Args:
        agent: PydanticAI agent to run
        request: FastAPI request with AG-UI protocol data
        deps: Dependencies containing AgentState
        on_complete: Optional callback invoked after the run completes

    Returns:
        StreamingResponse with AG-UI protocol events (state updates handled automatically)
    """
    logger.info("Handling AG-UI request with thinking block capture")

    # Get the original response
    response = await _handle_ag_ui_request(agent, request, deps=deps, on_complete=on_complete)

    # After the response completes, extract thinking from conversation history
    # Wrap the response to extract thinking and update state
    return StreamingResponse(
        _inject_thinking_extraction(response.body_iterator, deps.state, agent),
        media_type=response.media_type,
        headers=dict(response.headers),
    )


async def _inject_thinking_extraction(
    stream: AsyncIterator[bytes],
    state: AgentState,
    agent: Agent,
) -> AsyncIterator[bytes]:
    """Inject thinking block extraction into the response stream.

    This yields all original chunks, then after the stream completes,
    extracts thinking blocks from the conversation history and stores them in state.
    State updates are automatically emitted via AG-UI protocol.

    Args:
        stream: Original AG-UI response stream
        state: AgentState to store thinking blocks
        agent: Agent instance to access conversation history

    Yields:
        Original bytes (state updates handled automatically by PydanticAI)
    """
    # Track seen thinking blocks to avoid duplicates
    seen_thinking_hashes = set()

    # Process stream and pass through all chunks
    try:
        async for chunk in stream:
            yield chunk
    except Exception as e:
        logger.error("❌ Error while streaming AG-UI response", exc_info=True)
        error_message = str(e).strip() or "Unknown error"
        if len(error_message) > MAX_ERROR_MESSAGE_LENGTH:
            error_message = f"{error_message[:MAX_ERROR_MESSAGE_LENGTH]}..."
        error_event = {"type": "RUN_ERROR", "error": error_message}
        try:
            yield f"data: {json.dumps(error_event)}\n\n".encode()
        except Exception as encode_error:
            logger.error(
                "❌ Failed to emit structured error event for AG-UI response",
                exc_info=True,
            )
            # Fallback: attempt to send a minimal, hard-coded error payload
            fallback_event = {
                "type": "RUN_ERROR",
                "error": "An unexpected error occurred.",
            }
            try:
                yield f"data: {json.dumps(fallback_event)}\n\n".encode()
            except Exception:
                # Last resort: yield a static, already-encoded error message
                yield (
                    b'data: {"type": "RUN_ERROR", "error": "An unexpected error occurred."}'
                    b"\n\n"
                )
    finally:
        # After stream completes, extract thinking from conversation history
        logger.info("Stream complete, extracting thinking blocks from conversation history")

        try:
            # Try multiple approaches to access conversation history
            messages_to_check = []

            # Approach 1: Check _current_messages (PydanticAI internal)
            if hasattr(agent, "_current_messages") and agent._current_messages:
                messages_to_check = agent._current_messages
                logger.info(f"Found {len(messages_to_check)} messages via _current_messages")
            # Approach 2: Check if there's a messages attribute
            elif hasattr(agent, "messages") and agent.messages:
                messages_to_check = agent.messages
                logger.info(f"Found {len(messages_to_check)} messages via messages")
            # Approach 3: Check state for messages
            elif hasattr(state, "messages") and state.messages:
                messages_to_check = state.messages
                logger.info(f"Found {len(messages_to_check)} messages via state.messages")

            # Extract thinking from messages and update state
            for msg in messages_to_check:
                logger.debug(f"Checking message type: {type(msg).__name__}")
                if isinstance(msg, ModelResponse):
                    # Check if this message has thinking parts
                    thinking_content = extract_thinking_from_response(msg)
                    if thinking_content:
                        logger.info(
                            f"Found {len(thinking_content)} thinking blocks in message"
                        )
                        for thinking in thinking_content:
                            # Use hash to avoid duplicates
                            thinking_hash = hash(thinking)
                            if thinking_hash in seen_thinking_hashes:
                                logger.debug("Skipping duplicate thinking block")
                                continue
                            seen_thinking_hashes.add(thinking_hash)

                            # Store thinking block in state (triggers automatic state_update event)
                            thinking_block = ThinkingBlock(
                                content=thinking,
                                timestamp=datetime.now(timezone.utc),
                            )
                            state.thinking_blocks.append(thinking_block)
                            logger.info(
                                f"✅ Stored thinking block in state ({len(thinking)} chars)"
                            )

        except Exception as e:
            logger.error(f"❌ Error extracting thinking blocks: {e}", exc_info=True)


def extract_thinking_from_response(response: ModelResponse) -> list[str]:
    """Extract thinking content from a model response.

    Args:
        response: ModelResponse from PydanticAI

    Returns:
        List of thinking content strings
    """
    thinking_blocks = []
    for part in response.parts:
        if isinstance(part, ThinkingPart):
            thinking_blocks.append(part.content)
    return thinking_blocks

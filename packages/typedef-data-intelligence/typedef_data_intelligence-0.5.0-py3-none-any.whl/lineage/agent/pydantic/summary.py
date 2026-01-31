"""Run summary generation using Fenic for thread context."""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any, List

import fenic as fc
from pydantic import BaseModel, Field
from pydantic_ai import ModelMessage

from lineage.backends.threads import RunSummary, ThreadsBackend

logger = logging.getLogger(__name__)


def format_messages_for_summary(messages: List[ModelMessage]) -> str:
    """Extract key parts of messages for summary generation.

    Args:
        messages: List of ModelMessage (ModelRequest | ModelResponse) from Pydantic AI

    Returns:
        Formatted string showing user requests and agent responses
    """
    conversation_parts = []

    for msg in messages:
        if msg.kind == "request":
            # ModelRequest - extract user prompt content
            for part in msg.parts:
                if part.part_kind == "system-prompt":
                    # Skip system prompts for summary
                    continue
                elif part.part_kind == "user-prompt":
                    # Extract text from user prompt
                    content = part.content
                    if isinstance(content, str):
                        conversation_parts.append(f"user: {content}")
                    # Note: UserPromptPart.content can also be Sequence[UserContent] for multimodal
                    # but for summary purposes, we focus on text
                elif part.part_kind == "tool-return":
                    tool_result = part.content
                    # Include tool results in summary context
                    tool_name = getattr(part, "tool_name", "unknown")
                    conversation_parts.append(f"tool_result ({tool_name}): {tool_result}")

        elif msg.kind == "response":
            # ModelResponse - extract text and tool calls
            text_content = msg.text
            if text_content:
                conversation_parts.append(f"assistant: {text_content}")

            # Include tool calls for context
            tool_calls = msg.tool_calls
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call.tool_name
                    conversation_parts.append(f"assistant (tool_call): {tool_name}")

    return "\n".join(conversation_parts) if conversation_parts else "No conversation found"

class SummaryResponse(BaseModel):
    """Response model for conversation summary generation.

    Contains a summary and title extracted from a conversation thread.
    """

    summary: str = Field(description="A concise summary of the conversation.")
    title: str = Field(description="A title for the conversation.")

async def generate_and_save_run_summary(
    messages: List[ModelMessage],
    thread_id: str,
    run_id: str,
    thread_backend: ThreadsBackend,
) -> SummaryResponse:
    """Generate and save a run summary to the thread store."""
    summary = await generate_run_summary(messages)
    thread_backend.save_run_summary(thread_id, RunSummary(
        run_id=run_id,
        timestamp=datetime.now(tz=UTC),
        title=summary.title,
        summary=summary.summary,
    ))


async def generate_run_summary(
    messages: List[Any],
) -> SummaryResponse:
    """Generate natural language summary of a run using Fenic.

    Uses Fenic's semantic.extract to create a concise summary from a DataFrame
    containing the conversation and artifacts.

    Args:
        messages: List of messages from the conversation
        artifacts: List of artifact dicts created during the run

    Returns:
        SummaryResponse containing summary and title
    """
    conversation = format_messages_for_summary(messages)


    # Run Fenic extraction in thread pool (Fenic is sync)
    def run_fenic_extraction():
        # Create session with Anthropic model
        session = fc.Session.get_or_create(
            fc.SessionConfig(
                app_name="thread_summary",
                semantic=fc.SemanticConfig(
                    language_models={
                        "default": fc.OpenAILanguageModel(
                            model_name="gpt-5-nano",
                            rpm=500,
                            tpm=125_000,
                        )
                    },
                    default_language_model="default"
                )
            )
        )
        

        
        try:
            # Create DataFrame with conversation data
            df = session.create_dataframe({"conversation_data": [conversation]})
            prompt = """
            You will be provided a conversation history between a user and a data intelligence agent.
            Your job is to provide a concise summary of the conversation.
            The summary should be a 2-5 sentence summary covering: 
                (1) what the user asked for, 
                (2) what the agent did, 
                (3) what was created/accomplished. 
                (4) note the exact details (name, type, id) of the artifacts (reports, etc.) created.
                
                Keep it brief and factual. Focus on outcomes, not implementation details.
            The conversation summary is:
            {{conversation_data}}
            """
            # Use semantic.extract to generate summary
            result_df = df.select(
                fc.semantic.map(
                    prompt, 
                    conversation_data=fc.col("conversation_data"),
                    response_format=SummaryResponse,
                ).alias("summary")
            )

            # Collect the result
            result = result_df.to_pylist()[0]
            return SummaryResponse.model_validate(result['summary'])

        finally:
            session.stop()

    try:
        summary = await asyncio.to_thread(run_fenic_extraction)
        logger.info(f"Generated run summary: title={summary.title}, summary={summary.summary[:500]}...")
        return summary
    except Exception as e:
        logger.error(f"Error generating run summary with Fenic: {e}", exc_info=True)
        # Fallback summary
        return "Agent run completed"

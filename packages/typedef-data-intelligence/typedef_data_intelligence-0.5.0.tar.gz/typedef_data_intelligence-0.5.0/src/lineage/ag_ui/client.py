"""AG-UI protocol client.

This module provides a shared client for interacting with AG-UI agent endpoints.
"""
import inspect
import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
)

import httpx
from ag_ui.core import RunAgentInput

logger = logging.getLogger(__name__)


@dataclass
class AGUIRunResult:
    """Aggregated result from an AG-UI run."""
    text_response: str = ""
    raw_events: List[Dict[str, Any]] = field(default_factory=list)
    tool_events: List[Dict[str, Any]] = field(default_factory=list)


class AGUIRequestError(RuntimeError):
    """Error raised when an AG-UI request fails."""

    def __init__(self, url: str, status_code: Optional[int], detail: str):
        """Initialize the request error."""
        self.url = url
        self.status_code = status_code
        self.detail = detail
        status = f"HTTP {status_code}" if status_code is not None else "Request error"
        super().__init__(f"{status} for {url}: {detail}")


class AGUIClient:
    """Client for interacting with AG-UI agent endpoints."""

    def __init__(
        self, 
        base_url: str, 
        timeout: float = None,
        default_headers: Optional[Dict[str, str]] = None
    ):
        """Initialize the client.
        
        Args:
            base_url: Base URL of the AG-UI API (e.g. http://localhost:8000)
            timeout: Request timeout in seconds (default None for streaming)
            default_headers: Optional default headers to send with requests
        """
        self.base_url = base_url.rstrip("/")
        self.default_headers = default_headers or {}
        self.http_client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()

    async def stream_agent(
        self,
        agent_name: str,
        message: str,
        thread_id: str,
        run_id: str,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        forwarded_props: Optional[Dict[str, Any]] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream events from an agent run.

        Args:
            agent_name: Name of agent endpoint (analyst, quality, copilot)
            message: User message to send (ignored if messages provided)
            thread_id: Conversation thread ID
            run_id: Unique run ID
            user_id: Optional user ID for headers
            org_id: Optional organization ID for headers
            forwarded_props: Optional extra properties to forward
            messages: Optional full message history (if provided, overrides message param)

        Yields:
            Parsed SSE/NDJSON events
        """
        url = f"{self.base_url}/agents/{agent_name}"
        
        # Build headers
        headers = {**self.default_headers, "Accept": "text/event-stream"}
        if user_id:
            headers["X-User-Id"] = user_id
        if org_id:
            headers["X-Org-Id"] = org_id

        # Use provided messages or create single-message list
        if messages is not None:
            input_messages = messages
        else:
            input_messages = [
                {
                    "role": "user",
                    "content": message,
                    "id": str(uuid.uuid4()),
                }
            ]

        # Construct payload
        input_data = RunAgentInput(
            thread_id=thread_id,
            run_id=run_id,
            messages=input_messages,
            tools=[],
            context=[],
            state={},
            forwarded_props=forwarded_props or {},
        )

        try:
            async with self.http_client.stream(
                "POST",
                url,
                json=input_data.model_dump(mode="json"),
                headers=headers,
            ) as response:
                if response.status_code != 200:
                    raw_body = await response.aread()
                    detail = raw_body.decode(errors="replace").strip()
                    logger.error(f"Error connecting to {url}: {response.status_code} {detail}")
                    raise AGUIRequestError(url, response.status_code, detail or "Unknown error")

                logger.info(f"Connected to {url}, status={response.status_code}")

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    if line.startswith("data: "):
                        data = line[6:].strip()
                        if not data or data == "[DONE]":
                            continue
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse event data: {data}")
        except httpx.HTTPError as exc:
            detail = str(exc)
            logger.error(f"HTTP error connecting to {url}: {detail}")
            raise AGUIRequestError(url, None, detail) from exc

    async def run_agent_aggregated(
        self,
        agent_name: str,
        message: str,
        thread_id: str,
        run_id: str,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        forwarded_props: Optional[Dict[str, Any]] = None,
        event_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    ) -> AGUIRunResult:
        """Run agent and return aggregated result (useful for non-streaming clients)."""
        parser = _AGUIEventParser()
        
        async for event in self.stream_agent(
            agent_name, message, thread_id, run_id, user_id, org_id, forwarded_props
        ):
            if event_callback:
                maybe = event_callback(event)
                if inspect.isawaitable(maybe):
                    await maybe
            parser.ingest(event)
            
        return parser.finalize()


class _AGUIEventParser:
    """Helper for condensing AG-UI events into aggregated results."""

    def __init__(self) -> None:
        self._text_chunks: List[str] = []
        self._raw_events: List[Dict[str, Any]] = []
        self._assistant_messages: List[Dict[str, Any]] = []

    def ingest(self, event: Dict[str, Any]) -> None:
        self._raw_events.append(event)
        event_type = event.get("type")
        
        if event_type in {"TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_CHUNK"}:
            delta = event.get("delta") or ""
            self._text_chunks.append(delta)
            
        elif event_type == "TEXT_MESSAGE_END":
            # Flush buffer on explicit end (though START also handles it)
            pass
            
        elif event_type == "TEXT_MESSAGE_START":
            # reset chunk buffer for new assistant turn
            if self._text_chunks:
                self._assistant_messages.append(
                    {
                        "role": "assistant",
                        "content": "".join(self._text_chunks).strip(),
                    }
                )
                self._text_chunks = []
                
        elif event_type == "TOOL_CALL_RESULT":
            # Capture tool outputs as assistant messages? 
            # Usually tool outputs are role="tool", but let's keep logic aligned with original Slack client for now
            # Or maybe we just want the final text.
            pass

    def finalize(self) -> AGUIRunResult:
        """Return aggregated result."""
        if self._text_chunks:
            self._assistant_messages.append(
                {"role": "assistant", "content": "".join(self._text_chunks).strip()}
            )
            self._text_chunks = []

        text = "\n\n".join(
            msg["content"] for msg in self._assistant_messages if msg.get("content")
        )
        
        return AGUIRunResult(
            text_response=text,
            raw_events=self._raw_events,
            tool_events=[
                event for event in self._raw_events if event.get("type", "").startswith("TOOL")
            ],
        )


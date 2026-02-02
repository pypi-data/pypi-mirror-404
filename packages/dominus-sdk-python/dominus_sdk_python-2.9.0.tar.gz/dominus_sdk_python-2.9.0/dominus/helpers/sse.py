"""
SSE (Server-Sent Events) streaming helper.

Provides async generator for parsing SSE streams from httpx responses.
Used by dominus.ai.stream_agent(), dominus.ai.complete_stream(), etc.
"""
import json
from typing import Any, AsyncGenerator, Callable, Dict, Optional
import httpx


async def stream_sse(
    response: httpx.Response,
    on_event: Optional[Callable[[Dict[str, Any]], None]] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Parse SSE stream from httpx response.

    SSE format:
        event: event_name (optional)
        data: json_payload
        (blank line)

    Special handling:
        - data: [DONE] signals end of stream
        - Empty data lines are skipped
        - Non-JSON data lines are yielded as {"raw": data}

    Args:
        response: httpx.Response with streaming enabled
        on_event: Optional callback for each event (called before yield)

    Yields:
        Parsed JSON data from each SSE event
    """
    event_type = None
    data_buffer = []

    async for line in response.aiter_lines():
        line = line.strip()

        # Empty line = end of event
        if not line:
            if data_buffer:
                data_str = "\n".join(data_buffer)
                data_buffer = []

                # Check for stream end signal
                if data_str == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    # Non-JSON data - wrap in raw field
                    data = {"raw": data_str}

                # Add event type if present
                if event_type:
                    data["_event"] = event_type
                    event_type = None

                if on_event:
                    on_event(data)
                yield data
            continue

        # Parse SSE fields
        if line.startswith("event:"):
            event_type = line[6:].strip()
        elif line.startswith("data:"):
            data_str = line[5:].strip()
            # Handle immediate [DONE] on same line
            if data_str == "[DONE]":
                break
            data_buffer.append(data_str)
        elif line.startswith("id:"):
            # Event ID - we don't track this currently
            pass
        elif line.startswith("retry:"):
            # Retry timeout - we don't use this currently
            pass
        elif line.startswith(":"):
            # Comment line - ignore
            pass


async def collect_stream(
    response: httpx.Response,
    on_event: Optional[Callable[[Dict[str, Any]], None]] = None
) -> Dict[str, Any]:
    """
    Collect all SSE events and return final aggregated result.

    Useful for collecting streaming responses into a single result.
    Looks for final_response or combines content deltas.

    Args:
        response: httpx.Response with streaming enabled
        on_event: Optional callback for each event

    Returns:
        Aggregated result dict with:
        - final_response: The last complete response (if present)
        - content: Concatenated content from all deltas
        - chunks: List of all chunks received
    """
    chunks = []
    content_parts = []
    final_response = None

    async for chunk in stream_sse(response, on_event):
        chunks.append(chunk)

        # Collect content deltas
        if "content" in chunk:
            content_parts.append(chunk["content"])
        elif "delta" in chunk and "content" in chunk["delta"]:
            content_parts.append(chunk["delta"]["content"])

        # Capture final response if present
        if "final_response" in chunk:
            final_response = chunk["final_response"]

    return {
        "final_response": final_response,
        "content": "".join(content_parts),
        "chunks": chunks,
        "chunk_count": len(chunks)
    }

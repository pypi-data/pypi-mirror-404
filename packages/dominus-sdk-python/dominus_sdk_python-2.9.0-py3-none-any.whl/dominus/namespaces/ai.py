"""
AI Namespace - Unified agent-runtime operations.

Provides agent execution, LLM completions, RAG corpus management,
artifacts, speech services, and workflow orchestration.

All operations go through /api/* endpoints on the agent-runtime service,
proxied via the gateway at /svc/*.

Usage:
    from dominus import dominus

    # Agent execution
    result = await dominus.ai.run_agent(
        conversation_id="conv-123",
        system_prompt="You are helpful.",
        user_prompt="Hello!"
    )

    # Streaming agent execution
    async for chunk in dominus.ai.stream_agent(
        conversation_id="conv-123",
        system_prompt="You are helpful.",
        user_prompt="Tell me a story"
    ):
        print(chunk.get("content", ""), end="", flush=True)

    # LLM completion
    result = await dominus.ai.complete(
        messages=[{"role": "user", "content": "Hello"}],
        provider="claude",
        model="claude-sonnet-4-5"
    )

    # RAG operations
    await dominus.ai.rag.ensure("my-corpus")
    await dominus.ai.rag.upsert("my-corpus", "doc-1", content="Important info")
    results = await dominus.ai.rag.search("my-corpus", query="important")

    # Speech
    text = await dominus.ai.stt(audio_bytes, format="wav")
    audio = await dominus.ai.tts("Hello world", voice="nova")
"""
import asyncio
import time
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..start import Dominus


# ========================================
# Gateway-routed API helper
# ========================================

class GatewayMixin:
    """
    Mixin that provides gateway-routed API calls.

    All AI namespace methods route through the gateway's /svc/* endpoints
    which proxy to agent-runtime's /api/* endpoints.
    """
    _client: "Dominus"

    async def _api(
        self,
        endpoint: str,
        method: str = "POST",
        body: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make gateway-routed API request."""
        return await self._client._request(
            endpoint=endpoint,
            method=method,
            body=body,
            use_gateway=True
        )

    async def _api_stream(
        self,
        endpoint: str,
        body: Optional[Dict[str, Any]] = None,
        on_chunk: Optional[Any] = None,
        timeout: float = 300.0
    ):
        """Make gateway-routed streaming request."""
        async for chunk in self._client._stream_request(
            endpoint=endpoint,
            body=body,
            on_chunk=on_chunk,
            timeout=timeout,
            use_gateway=True
        ):
            yield chunk

    async def _api_upload(
        self,
        endpoint: str,
        file_bytes: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        additional_fields: Optional[Dict[str, str]] = None,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """Make gateway-routed binary upload."""
        return await self._client._binary_upload(
            endpoint=endpoint,
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
            additional_fields=additional_fields,
            timeout=timeout,
            use_gateway=True
        )

    async def _api_download(
        self,
        endpoint: str,
        body: Optional[Dict[str, Any]] = None,
        timeout: float = 60.0
    ) -> bytes:
        """Make gateway-routed binary download."""
        return await self._client._binary_download(
            endpoint=endpoint,
            body=body,
            timeout=timeout,
            use_gateway=True
        )


# ========================================
# RAG Sub-namespace
# ========================================

class RagSubNamespace(GatewayMixin):
    """
    RAG corpus management sub-namespace.

    Provides corpus CRUD, document ingestion, and semantic search.
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    async def list(self) -> List[Dict[str, Any]]:
        """List all corpora."""
        result = await self._api(
            endpoint="/api/rag",
            method="GET"
        )
        return result.get("corpora", result) if isinstance(result, dict) else result

    async def ensure(
        self,
        slug: str,
        description: Optional[str] = None,
        embedding_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ensure corpus exists (create if not).

        Args:
            slug: Corpus identifier (URL-safe string)
            description: Optional description
            embedding_model: Optional embedding model override
        """
        body: Dict[str, Any] = {}
        if description:
            body["description"] = description
        if embedding_model:
            body["embedding_model"] = embedding_model

        return await self._api(
            endpoint=f"/api/rag/{slug}/ensure",
            body=body if body else {}
        )

    async def stats(self, slug: str) -> Dict[str, Any]:
        """Get corpus statistics."""
        return await self._api(
            endpoint=f"/api/rag/{slug}/stats",
            method="GET"
        )

    async def drop(self, slug: str) -> Dict[str, Any]:
        """Drop/delete a corpus."""
        return await self._api(
            endpoint=f"/api/rag/{slug}",
            method="DELETE"
        )

    async def entries(
        self,
        slug: str,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List entries in a corpus."""
        body: Dict[str, Any] = {"limit": limit, "offset": offset}
        if category:
            body["category"] = category

        return await self._api(
            endpoint=f"/api/rag/{slug}/entries",
            body=body
        )

    async def upsert(
        self,
        slug: str,
        identifier: str,
        content: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        source_reference: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upsert a single entry.

        Args:
            slug: Corpus identifier
            identifier: Entry identifier (unique within corpus)
            content: Text content to embed (stored as content_markdown)
            name: Optional human-readable name
            description: Optional brief description
            category: Optional category for filtering
            subcategory: Optional subcategory
            source_reference: Optional source attribution
            metadata: Optional metadata dict
        """
        body: Dict[str, Any] = {"content_markdown": content}
        if name:
            body["name"] = name
        if description:
            body["description"] = description
        if category:
            body["category"] = category
        if subcategory:
            body["subcategory"] = subcategory
        if source_reference:
            body["source_reference"] = source_reference
        if metadata:
            body["metadata"] = metadata

        return await self._api(
            endpoint=f"/api/rag/{slug}/{identifier}",
            method="PUT",
            body=body
        )

    async def get(self, slug: str, identifier: str) -> Dict[str, Any]:
        """Get a specific entry."""
        return await self._api(
            endpoint=f"/api/rag/{slug}/{identifier}",
            method="GET"
        )

    async def delete(self, slug: str, identifier: str) -> Dict[str, Any]:
        """Delete an entry."""
        return await self._api(
            endpoint=f"/api/rag/{slug}/{identifier}",
            method="DELETE"
        )

    async def bulk_upsert(
        self,
        slug: str,
        entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Bulk upsert entries.

        Args:
            slug: Corpus identifier
            entries: List of entry dicts with:
                - identifier: string (required)
                - content: string (required) - Will be sent as content_markdown
                - name: string (optional)
                - description: string (optional)
                - category: string (optional)
                - subcategory: string (optional)
                - source_reference: dict (optional)
                - metadata: dict (optional)

        Returns:
            Dict with "processed", "failed", "errors" counts
        """
        # Transform 'content' to 'content_markdown' for API compatibility
        transformed = []
        for entry in entries:
            e = dict(entry)
            if "content" in e and "content_markdown" not in e:
                e["content_markdown"] = e.pop("content")
            transformed.append(e)

        return await self._api(
            endpoint=f"/api/rag/{slug}/bulk",
            body={"entries": transformed}
        )

    async def search(
        self,
        slug: str,
        query: str,
        limit: int = 10,
        threshold: Optional[float] = None,
        category: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search.

        Args:
            slug: Corpus identifier
            query: Search query text
            limit: Maximum results (default: 10)
            threshold: Optional similarity threshold (0-1)
            category: Optional category filter
            filters: Optional metadata filters

        Returns:
            List of matching entries with scores
        """
        body: Dict[str, Any] = {
            "query": query,
            "limit": limit
        }
        if threshold is not None:
            body["threshold"] = threshold
        if category:
            body["category"] = category
        if filters:
            body["filters"] = filters

        result = await self._api(
            endpoint=f"/api/rag/{slug}/search",
            body=body
        )
        return result.get("results", result) if isinstance(result, dict) else result

    async def search_rerank(
        self,
        slug: str,
        query: str,
        limit: int = 10,
        rerank_model: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search with reranking.

        Args:
            slug: Corpus identifier
            query: Search query text
            limit: Maximum results
            rerank_model: Optional reranker model
        """
        body: Dict[str, Any] = {
            "query": query,
            "limit": limit
        }
        if rerank_model:
            body["rerank_model"] = rerank_model

        result = await self._api(
            endpoint=f"/api/rag/{slug}/search/rerank",
            body=body
        )
        return result.get("results", result) if isinstance(result, dict) else result

    async def ingest(
        self,
        slug: str,
        content: bytes,
        filename: str,
        content_type: Optional[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Dict[str, Any]:
        """
        Ingest a document (PDF, DOCX, TXT, etc.) into corpus.

        Args:
            slug: Corpus identifier
            content: Document bytes
            filename: Original filename
            content_type: MIME type (auto-detected if not provided)
            chunk_size: Chunk size for splitting (default: 1000 chars)
            chunk_overlap: Overlap between chunks (default: 200 chars)
        """
        return await self._api_upload(
            endpoint=f"/api/rag/{slug}/ingest",
            file_bytes=content,
            filename=filename,
            content_type=content_type or "application/octet-stream",
            additional_fields={
                "chunk_size": str(chunk_size),
                "chunk_overlap": str(chunk_overlap)
            }
        )

    async def delete_document(self, slug: str, document_id: str) -> Dict[str, Any]:
        """Delete a document and all its chunks."""
        return await self._api(
            endpoint=f"/api/rag/{slug}/document/{document_id}",
            method="DELETE"
        )


# ========================================
# Artifacts Sub-namespace
# ========================================

class ArtifactsSubNamespace(GatewayMixin):
    """
    Artifacts sub-namespace for conversation artifact management.
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    async def get(
        self,
        artifact_id: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Get artifact by ID."""
        return await self._api(
            endpoint=f"/api/agent/artifacts/{artifact_id}?conversation_id={conversation_id}",
            method="GET"
        )

    async def create(
        self,
        name: str,
        content: str,
        conversation_id: str,
        artifact_type: str = "text/plain",
        is_base64: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new artifact.

        Args:
            name: Artifact key/filename
            content: Artifact content (text or base64-encoded for binary)
            conversation_id: Associated conversation ID
            artifact_type: MIME content type (e.g., "text/plain", "text/html", "image/png")
            is_base64: If True, content is base64-encoded binary
            metadata: Optional metadata dict (not stored, for SDK use)
        """
        body: Dict[str, Any] = {
            "key": name,
            "content": content,
            "conversation_id": conversation_id,
            "content_type": artifact_type,
            "is_base64": is_base64
        }

        return await self._api(
            endpoint="/api/agent/artifacts",
            body=body
        )

    async def list(
        self,
        conversation_id: str
    ) -> List[Dict[str, Any]]:
        """List artifacts for a conversation."""
        result = await self._api(
            endpoint=f"/api/agent/artifacts?conversation_id={conversation_id}",
            method="GET"
        )
        return result.get("artifacts", result) if isinstance(result, dict) else result

    async def delete(
        self,
        artifact_id: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Delete an artifact."""
        return await self._api(
            endpoint=f"/api/agent/artifacts/{artifact_id}?conversation_id={conversation_id}",
            method="DELETE"
        )


# ========================================
# Results Sub-namespace
# ========================================

class ResultsSubNamespace(GatewayMixin):
    """
    Async results sub-namespace for polling async operation results.
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    async def get(self, result_key: str) -> Dict[str, Any]:
        """
        Get async result by key.

        Args:
            result_key: Result key from async operation

        Returns:
            Dict with "status" (pending|running|completed|failed),
            "result" (if completed), "error" (if failed)
        """
        return await self._api(
            endpoint=f"/api/results/{result_key}",
            method="GET"
        )

    async def poll(
        self,
        result_key: str,
        interval: float = 1.0,
        timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Poll for result until completion or timeout.

        Args:
            result_key: Result key from async operation
            interval: Polling interval in seconds (default: 1s)
            timeout: Maximum wait time in seconds (default: 300s)

        Returns:
            Final result dict

        Raises:
            TimeoutError: If timeout exceeded
            RuntimeError: If operation failed
        """
        start = time.time()
        while time.time() - start < timeout:
            result = await self.get(result_key)
            status = result.get("status", "unknown")

            if status == "completed":
                return result
            elif status == "failed":
                raise RuntimeError(f"Operation failed: {result.get('error', 'Unknown error')}")

            await asyncio.sleep(interval)

        raise TimeoutError(f"Result polling timed out after {timeout}s")


# ========================================
# Workflow Sub-namespace
# ========================================

class WorkflowSubNamespace(GatewayMixin):
    """
    Multi-agent workflow orchestration sub-namespace.
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    async def execute(
        self,
        workflow_id: str,
        input: Dict[str, Any],
        conversation_id: Optional[str] = None,
        mode: str = "blocking",
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a multi-agent workflow.

        Args:
            workflow_id: Workflow identifier
            input: Workflow input data
            conversation_id: Optional conversation ID for context
            mode: Execution mode ("blocking", "streaming", "async")
            webhook_url: Optional webhook for completion notification

        Returns:
            Dict with "execution_id", "status", "output" (if blocking)
        """
        body: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "input": input,
            "mode": mode
        }
        if conversation_id:
            body["conversation_id"] = conversation_id
        if webhook_url:
            body["webhook_url"] = webhook_url

        return await self._api(
            endpoint="/api/orchestration/execute",
            body=body
        )

    async def validate(
        self,
        workflow_definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a workflow definition.

        Args:
            workflow_definition: Workflow definition dict

        Returns:
            Dict with "valid", "errors" (if invalid)
        """
        return await self._api(
            endpoint="/api/orchestration/validate",
            body={"definition": workflow_definition}
        )

    async def messages(
        self,
        execution_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages from an execution."""
        result = await self._api(
            endpoint=f"/api/orchestration/messages/{execution_id}",
            body={"limit": limit, "offset": offset}
        )
        return result.get("messages", result) if isinstance(result, dict) else result

    async def events(
        self,
        execution_id: str,
        from_timestamp: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Replay events from an execution."""
        body: Dict[str, Any] = {}
        if from_timestamp:
            body["from"] = from_timestamp

        result = await self._api(
            endpoint=f"/api/orchestration/events/{execution_id}",
            body=body if body else None
        )
        return result.get("events", result) if isinstance(result, dict) else result

    async def status(self, execution_id: str) -> Dict[str, Any]:
        """Get execution status."""
        return await self._api(
            endpoint=f"/api/orchestration/status/{execution_id}",
            method="GET"
        )

    async def output(self, execution_id: str) -> Dict[str, Any]:
        """Get final execution output."""
        return await self._api(
            endpoint=f"/api/orchestration/output/{execution_id}",
            method="GET"
        )


# ========================================
# Main AI Namespace
# ========================================

class AiNamespace(GatewayMixin):
    """
    Unified AI namespace for agent-runtime operations.

    Contains:
    - Agent execution (run_agent, stream_agent, run_agent_async)
    - LLM completions (complete, complete_stream, complete_async)
    - Speech (stt, tts)
    - Conversation history (history)
    - Pre-flight setup (setup)
    - Sub-namespaces: rag, artifacts, results, workflow
    """

    def __init__(self, client: "Dominus"):
        self._client = client

        # Initialize sub-namespaces
        self.rag = RagSubNamespace(client)
        self.artifacts = ArtifactsSubNamespace(client)
        self.results = ResultsSubNamespace(client)
        self.workflow = WorkflowSubNamespace(client)

    # ========================================
    # Agent Execution
    # ========================================

    async def run_agent(
        self,
        conversation_id: str,
        system_prompt: str,
        user_prompt: str,
        history_source: str = "conversation_id",
        inline_history: Optional[List[Dict[str, Any]]] = None,
        preloaded_context: Optional[str] = None,
        artifact_refs: Optional[List[str]] = None,
        tool_allowlist: Optional[List[str]] = None,
        guardrails: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        model: str = "claude-sonnet-4-5",
        tool_endpoint: Optional[str] = None,
        timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Execute agent with blocking wait.

        Args:
            conversation_id: Conversation identifier
            system_prompt: System prompt for the agent
            user_prompt: User input message
            history_source: "conversation_id" or "inline" (default: conversation_id)
            inline_history: History messages if history_source="inline"
            preloaded_context: Optional pre-loaded context string
            artifact_refs: Optional list of artifact IDs to include
            tool_allowlist: Optional list of tool names to enable
            guardrails: Optional guardrails config (max_steps, max_tool_calls, etc.)
            output_schema: Optional JSON Schema for structured output
            model: Model to use (default: claude-sonnet-4-5)
            tool_endpoint: Optional custom tool endpoint URL
            timeout: Request timeout in seconds (default: 300s)

        Returns:
            Dict with "conversation_id", "final_response", "machine_output",
            "artifacts_written", "telemetry"
        """
        body: Dict[str, Any] = {
            "conversation_id": conversation_id,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "history_source": history_source,
            "model": model
        }
        if inline_history:
            body["inline_history"] = inline_history
        if preloaded_context:
            body["preloaded_context"] = preloaded_context
        if artifact_refs:
            body["artifact_refs"] = artifact_refs
        if tool_allowlist:
            body["tool_allowlist"] = tool_allowlist
        if guardrails:
            body["guardrails"] = guardrails
        if output_schema:
            body["output_schema"] = output_schema
        if tool_endpoint:
            body["tool_endpoint"] = tool_endpoint

        return await self._api(
            endpoint="/api/agent/run",
            body=body
        )

    async def stream_agent(
        self,
        conversation_id: str,
        system_prompt: str,
        user_prompt: str,
        history_source: str = "conversation_id",
        inline_history: Optional[List[Dict[str, Any]]] = None,
        preloaded_context: Optional[str] = None,
        artifact_refs: Optional[List[str]] = None,
        tool_allowlist: Optional[List[str]] = None,
        guardrails: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        model: str = "claude-sonnet-4-5",
        tool_endpoint: Optional[str] = None,
        on_chunk: Optional[Callable[[Dict[str, Any]], None]] = None,
        timeout: float = 300.0
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute agent with SSE streaming.

        Args:
            conversation_id: Conversation identifier
            system_prompt: System prompt for the agent
            user_prompt: User input message
            history_source: "conversation_id" or "inline"
            inline_history: History messages if history_source="inline"
            preloaded_context: Optional pre-loaded context string
            artifact_refs: Optional list of artifact IDs
            tool_allowlist: Optional list of tool names
            guardrails: Optional guardrails config
            output_schema: Optional JSON Schema for structured output
            model: Model to use
            tool_endpoint: Optional custom tool endpoint URL
            on_chunk: Optional callback for each chunk
            timeout: Request timeout in seconds

        Yields:
            Streaming chunks with "type" and content
        """
        body: Dict[str, Any] = {
            "conversation_id": conversation_id,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "history_source": history_source,
            "model": model
        }
        if inline_history:
            body["inline_history"] = inline_history
        if preloaded_context:
            body["preloaded_context"] = preloaded_context
        if artifact_refs:
            body["artifact_refs"] = artifact_refs
        if tool_allowlist:
            body["tool_allowlist"] = tool_allowlist
        if guardrails:
            body["guardrails"] = guardrails
        if output_schema:
            body["output_schema"] = output_schema
        if tool_endpoint:
            body["tool_endpoint"] = tool_endpoint

        async for chunk in self._api_stream(
            endpoint="/api/agent/stream",
            body=body,
            on_chunk=on_chunk,
            timeout=timeout
        ):
            yield chunk

    async def run_agent_async(
        self,
        conversation_id: str,
        system_prompt: str,
        user_prompt: str,
        result_key: str,
        history_source: str = "conversation_id",
        inline_history: Optional[List[Dict[str, Any]]] = None,
        preloaded_context: Optional[str] = None,
        artifact_refs: Optional[List[str]] = None,
        tool_allowlist: Optional[List[str]] = None,
        guardrails: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        model: str = "claude-sonnet-4-5",
        tool_endpoint: Optional[str] = None,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fire-and-forget async execution.

        Returns immediately with result_key for polling via dominus.ai.results.get().

        Args:
            conversation_id: Conversation identifier
            system_prompt: System prompt for the agent
            user_prompt: User input message
            result_key: Key for retrieving result later
            history_source: "conversation_id" or "inline"
            inline_history: History messages if history_source="inline"
            preloaded_context: Optional pre-loaded context string
            artifact_refs: Optional list of artifact IDs
            tool_allowlist: Optional list of tool names
            guardrails: Optional guardrails config
            output_schema: Optional JSON Schema
            model: Model to use
            tool_endpoint: Optional custom tool endpoint URL
            webhook_url: Optional webhook for completion notification

        Returns:
            Dict with "result_key" for polling
        """
        body: Dict[str, Any] = {
            "conversation_id": conversation_id,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "result_key": result_key,
            "history_source": history_source,
            "model": model
        }
        if inline_history:
            body["inline_history"] = inline_history
        if preloaded_context:
            body["preloaded_context"] = preloaded_context
        if artifact_refs:
            body["artifact_refs"] = artifact_refs
        if tool_allowlist:
            body["tool_allowlist"] = tool_allowlist
        if guardrails:
            body["guardrails"] = guardrails
        if output_schema:
            body["output_schema"] = output_schema
        if tool_endpoint:
            body["tool_endpoint"] = tool_endpoint
        if webhook_url:
            body["webhook_url"] = webhook_url

        return await self._api(
            endpoint="/api/agent/run-async",
            body=body
        )

    # ========================================
    # Conversation History
    # ========================================

    async def history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history.

        Args:
            conversation_id: Conversation identifier
            limit: Maximum messages to return (default: 50)

        Returns:
            List of history messages
        """
        result = await self._api(
            endpoint=f"/api/agent/history/{conversation_id}?limit={limit}",
            method="GET"
        )
        return result.get("messages", result) if isinstance(result, dict) else result

    # ========================================
    # LLM Completions
    # ========================================

    async def complete(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        provider: str = "claude",
        model: str = "claude-sonnet-4-5",
        conversation_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        timeout: float = 120.0
    ) -> Dict[str, Any]:
        """
        Blocking LLM completion.

        Args:
            messages: List of message dicts with "role" and "content" (optional)
            provider: LLM provider ("claude" or "openai")
            model: Model identifier
            conversation_id: Optional conversation ID
            temperature: Temperature (0-2, default: 0.7)
            max_tokens: Maximum tokens to generate
            system_prompt: System prompt (required if messages not provided)
            user_prompt: User prompt (required if messages not provided)
            timeout: Request timeout in seconds

        Returns:
            Dict with "content", "model", "usage", etc.

        Note:
            Either provide `messages` OR both `system_prompt` and `user_prompt`.
            If messages provided, the last user message becomes user_prompt,
            and system messages become system_prompt.
        """
        # Convert messages to system_prompt/user_prompt if needed
        if messages and not user_prompt:
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt = msg.get("content", system_prompt)
                elif msg.get("role") == "user":
                    user_prompt = msg.get("content")

        if not system_prompt:
            system_prompt = "You are a helpful assistant."

        if not user_prompt:
            raise ValueError("Either 'messages' with a user message or 'user_prompt' is required")

        body: Dict[str, Any] = {
            "provider": provider,
            "model": model,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "temperature": temperature
        }
        if conversation_id:
            body["conversation_id"] = conversation_id
        if max_tokens:
            body["max_tokens"] = max_tokens

        return await self._api(
            endpoint="/api/llm/complete",
            body=body
        )

    async def complete_stream(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        provider: str = "claude",
        model: str = "claude-sonnet-4-5",
        conversation_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        on_chunk: Optional[Callable[[Dict[str, Any]], None]] = None,
        timeout: float = 120.0
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streaming LLM completion.

        Args:
            messages: List of message dicts (optional)
            provider: LLM provider
            model: Model identifier
            conversation_id: Optional conversation ID
            temperature: Temperature (0-2)
            max_tokens: Maximum tokens
            system_prompt: System prompt (required if messages not provided)
            user_prompt: User prompt (required if messages not provided)
            on_chunk: Optional callback for each chunk
            timeout: Request timeout

        Yields:
            Streaming chunks with "content" delta
        """
        # Convert messages to system_prompt/user_prompt if needed
        if messages and not user_prompt:
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt = msg.get("content", system_prompt)
                elif msg.get("role") == "user":
                    user_prompt = msg.get("content")

        if not system_prompt:
            system_prompt = "You are a helpful assistant."

        if not user_prompt:
            raise ValueError("Either 'messages' with a user message or 'user_prompt' is required")

        body: Dict[str, Any] = {
            "provider": provider,
            "model": model,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "temperature": temperature
        }
        if conversation_id:
            body["conversation_id"] = conversation_id
        if max_tokens:
            body["max_tokens"] = max_tokens

        async for chunk in self._api_stream(
            endpoint="/api/llm/stream",
            body=body,
            on_chunk=on_chunk,
            timeout=timeout
        ):
            yield chunk

    async def complete_async(
        self,
        messages: List[Dict[str, Any]],
        result_key: str,
        provider: str = "claude",
        model: str = "claude-sonnet-4-5",
        conversation_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Async LLM completion (fire-and-forget).

        Args:
            messages: List of message dicts
            result_key: Key for retrieving result later
            provider: LLM provider
            model: Model identifier
            conversation_id: Optional conversation ID
            temperature: Temperature
            max_tokens: Maximum tokens
            system_prompt: Optional system prompt
            webhook_url: Optional webhook for completion

        Returns:
            Dict with "result_key" for polling
        """
        body: Dict[str, Any] = {
            "messages": messages,
            "result_key": result_key,
            "provider": provider,
            "model": model,
            "temperature": temperature
        }
        if conversation_id:
            body["conversation_id"] = conversation_id
        if max_tokens:
            body["max_tokens"] = max_tokens
        if system_prompt:
            body["system_prompt"] = system_prompt
        if webhook_url:
            body["webhook_url"] = webhook_url

        return await self._api(
            endpoint="/api/llm/complete-async",
            body=body
        )

    # ========================================
    # Speech Services
    # ========================================

    async def stt(
        self,
        audio: bytes,
        format: str = "wav",
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Speech-to-text conversion.

        Args:
            audio: Raw audio bytes (NOT base64 encoded)
            format: Audio format (wav, mp3, webm, m4a, ogg, flac)
            language: Optional language code (auto-detected if not provided)

        Returns:
            Dict with "text", "confidence", "language", "duration"
        """
        return await self._api_upload(
            endpoint="/api/agent/stt",
            file_bytes=audio,
            filename=f"audio.{format}",
            content_type=f"audio/{format}",
            additional_fields={"language": language} if language else None
        )

    async def tts(
        self,
        text: str,
        voice: str = "nova",
        format: str = "mp3",
        speed: float = 1.0
    ) -> bytes:
        """
        Text-to-speech conversion.

        Args:
            text: Text to convert
            voice: Voice ID (nova, alloy, echo, fable, onyx, shimmer)
            format: Output format (mp3, wav, opus)
            speed: Speed multiplier (0.25-4.0)

        Returns:
            Raw audio bytes (NOT base64 encoded)
        """
        return await self._api_download(
            endpoint="/api/agent/tts",
            body={
                "text": text,
                "voice": voice,
                "format": format,
                "speed": speed
            }
        )

    # ========================================
    # Pre-flight Setup
    # ========================================

    async def setup(
        self,
        conversation_id: str,
        artifacts: Optional[List[Dict[str, Any]]] = None,
        rag_corpus: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Pre-flight session setup.

        Validates RAG corpus, pre-seeds artifacts, and stores context
        in Redis before agent execution.

        Args:
            conversation_id: Conversation identifier
            artifacts: Optional list of {"name", "content"} to pre-seed
            rag_corpus: Optional RAG corpus name to verify
            context: Optional context dict to store

        Returns:
            Dict with "ready", "conversation_id", "artifacts_created",
            "rag_corpus_verified", "warnings"
        """
        body: Dict[str, Any] = {
            "conversation_id": conversation_id
        }
        if artifacts:
            body["artifacts"] = artifacts
        if rag_corpus:
            body["rag_corpus"] = rag_corpus
        if context:
            body["context"] = context

        return await self._api(
            endpoint="/api/session/setup",
            body=body
        )

import asyncio
import ollama
import logging
import uuid
from typing import AsyncIterator

from livekit.agents.llm import (
    LLM,
    ChatContext,
    ChatChunk,
    ChatMessage,
    ChatRole,
    ChoiceDelta,
)

logger = logging.getLogger(__name__)


class AsyncIteratorContextManager:
    """Wrapper to make async iterator work as async context manager"""
    def __init__(self, async_iter: AsyncIterator[ChatChunk]):
        self._iter = async_iter
        self._iter_obj = None
    
    async def __aenter__(self):
        self._iter_obj = self._iter.__aiter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self._iter_obj, 'aclose'):
            await self._iter_obj.aclose()
        return False
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self._iter_obj is None:
            self._iter_obj = self._iter.__aiter__()
        return await self._iter_obj.__anext__()


class OllamaLLM(LLM):
    """
    Drop-in LLM adapter for Ollama compatible with LiveKit Agents SDK v1.3+.
    Implements BOTH required abstract methods: generate() and chat().
    """

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str = "http://host.docker.internal:11434",
    ):
        super().__init__()
        self._model = model
        self.base_url = base_url
        # Configure Ollama client to use custom host if provided
        import os
        ollama_host = os.getenv("OLLAMA_HOST")
        if ollama_host:
            import ollama
            # Set the host for Ollama client
            ollama.Client(host=ollama_host)

    @property
    def model(self):
        return self._model

    async def generate(self, messages: list[ChatMessage]) -> ChatMessage:
        """Non-streaming version used by AgentSession.generate_reply()"""
        payload = [
            {"role": m.role.value, "content": m.content}
            for m in messages
        ]

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: ollama.chat(
                    model=self.model,
                    messages=payload,
                    stream=False,
                )
            )

            content = result["message"]["content"]
            return ChatMessage(role=ChatRole.ASSISTANT, content=content)

        except Exception as e:
            logger.error(f"Ollama generate() error: {e}", exc_info=True)
            return ChatMessage(
                role=ChatRole.ASSISTANT,
                content="I'm having trouble responding. Could you repeat that?"
            )

    def chat(self, *, chat_ctx: ChatContext, **kwargs) -> AsyncIterator[ChatChunk]:
        """Streaming version used by AgentSession for real-time voice responses"""

        async def _stream():
            try:
                # ChatContext doesn't have .messages, iterate over items instead
                payload = []
                for msg in chat_ctx.items():
                    payload.append({
                        "role": msg.role.value,
                        "content": msg.content,
                    })

                loop = asyncio.get_event_loop()

                # Run synchronous streaming in a thread
                stream = await loop.run_in_executor(
                    None,
                    lambda: ollama.chat(
                        model=self.model,
                        messages=payload,
                        stream=True,
                    )
                )

                for chunk in stream:
                    if "message" in chunk and "content" in chunk["message"]:
                        content = chunk["message"]["content"]
                        
                        # ChatChunk requires id and delta as ChoiceDelta
                        yield ChatChunk(
                            id=str(uuid.uuid4()),
                            delta=ChoiceDelta(content=content)
                        )

                    if chunk.get("done"):
                        break

            except Exception as e:
                logger.error(f"Ollama chat() streaming error: {e}", exc_info=True)
                yield ChatChunk(
                    id=str(uuid.uuid4()),
                    delta=ChoiceDelta(content="Sorry, I had trouble generating my response.")
                )

        # Return wrapped async iterator that works as async context manager
        return AsyncIteratorContextManager(_stream())

import asyncio
import ollama
import logging
from typing import AsyncIterator

from livekit.agents.llm import (
    LLM,
    ChatContext,
    ChatChunk,
    ChatMessage,
    ChatRole,
)

logger = logging.getLogger(__name__)


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
                payload = []
                for m in chat_ctx.messages:
                    payload.append({
                        "role": m.role.value,
                        "content": m.content,
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

                        yield ChatChunk(
                            choices=[
                                ChatChunk.Choice(
                                    delta=ChatChunk.Choice.Delta(
                                        content=content
                                    )
                                )
                            ]
                        )

                    if chunk.get("done"):
                        break

            except Exception as e:
                logger.error(f"Ollama chat() streaming error: {e}", exc_info=True)
                yield ChatChunk(
                    choices=[
                        ChatChunk.Choice(
                            delta=ChatChunk.Choice.Delta(
                                content="Sorry, I had trouble generating my response."
                            )
                        )
                    ]
                )

        return _stream()

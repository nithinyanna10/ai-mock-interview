"""
LLM Client - Handles Ollama and other LLM provider integrations
"""

import logging
from typing import Optional, AsyncGenerator
import httpx
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with LLM providers (Ollama, OpenAI, etc.)"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config = self._load_config(config_path)
        self.llm_config = self.config.get("llm", {})
        self.provider = self.llm_config.get("provider", "ollama")
        self.model = self.llm_config.get("model", "chatgpt-120b-oss")
        self.base_url = self.llm_config.get("base_url", "http://localhost:11434")
        self.timeout = self.llm_config.get("timeout", 30)
        self.max_retries = self.llm_config.get("max_retries", 3)
        
    def _load_config(self, config_path: Optional[Path]) -> dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
            return {}
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        stream: bool = False
    ) -> AsyncGenerator[str, None]:
        """Generate response from LLM"""
        if self.provider == "ollama":
            async for chunk in self._generate_ollama(
                prompt, system_prompt, temperature, max_tokens, stream
            ):
                yield chunk
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    async def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        stream: bool
    ) -> AsyncGenerator[str, None]:
        """Generate response using Ollama"""
        url = f"{self.base_url}/api/chat"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if stream:
                    async with client.stream("POST", url, json=payload) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    import json
                                    data = json.loads(line)
                                    if "message" in data and "content" in data["message"]:
                                        content = data["message"]["content"]
                                        if content:
                                            yield content
                                    if data.get("done", False):
                                        break
                                except json.JSONDecodeError:
                                    continue
                else:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]
            except httpx.TimeoutException:
                logger.error(f"Ollama request timeout after {self.timeout}s")
                yield "I apologize, but I'm experiencing some technical difficulties. Could you please repeat that?"
            except httpx.HTTPStatusError as e:
                logger.error(f"Ollama HTTP error: {e}")
                yield "I apologize, but I'm experiencing some technical difficulties. Could you please repeat that?"
            except Exception as e:
                logger.error(f"Ollama error: {e}")
                yield "I apologize, but I'm experiencing some technical difficulties. Could you please repeat that?"
    
    async def generate_complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate complete response (non-streaming)"""
        full_response = ""
        async for chunk in self.generate(
            prompt, system_prompt, temperature, max_tokens, stream=False
        ):
            full_response += chunk
        return full_response


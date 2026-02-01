"""Chat completions resource"""

from typing import Optional, List, Literal, TYPE_CHECKING, Any, Dict, Iterator, AsyncIterator, Union
from xeno._types.responses import ChatCompletion, ChatCompletionChunk
import json

if TYPE_CHECKING:
    from xeno.client import Client, AsyncClient


class Completions:
    """
    Chat completions API.

    Usage:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response.choices[0].message.content)
    """

    def __init__(self, client: "Client"):
        self._client = client

    def create(
        self,
        messages: List[Dict[str, Any]],
        model: str = "gpt-4o",
        *,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, str]] = None,
        seed: Optional[int] = None,
        user: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Iterator[ChatCompletionChunk]]:
        """
        Create a chat completion.

        Args:
            messages: List of messages in the conversation
            model: Model to use (gpt-4o, claude-3.5-sonnet, gemini-pro, etc.)
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter
            max_tokens: Maximum tokens to generate
            stop: Stop sequences
            stream: If True, stream the response
            tools: List of tools/functions the model can call
            tool_choice: How to select tools
            response_format: Response format specification
            seed: Random seed for reproducibility
            user: Unique user identifier

        Returns:
            ChatCompletion or Iterator of ChatCompletionChunk if streaming
        """
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if stop is not None:
            payload["stop"] = stop
        if stream:
            payload["stream"] = True
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        if response_format is not None:
            payload["response_format"] = response_format
        if seed is not None:
            payload["seed"] = seed
        if user is not None:
            payload["user"] = user

        payload.update(kwargs)

        if stream:
            return self._stream(payload)

        response = self._client._request("POST", "/chat/completions", json=payload)
        return ChatCompletion(**response)

    def _stream(self, payload: Dict[str, Any]) -> Iterator[ChatCompletionChunk]:
        """Stream chat completion chunks"""
        response = self._client._request("POST", "/chat/completions", json=payload, stream=True)

        for line in response:
            if isinstance(line, bytes):
                line = line.decode("utf-8")
            line = line.strip()
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    yield ChatCompletionChunk(**chunk)
                except json.JSONDecodeError:
                    continue


class AsyncCompletions:
    """Async chat completions API"""

    def __init__(self, client: "AsyncClient"):
        self._client = client

    async def create(
        self,
        messages: List[Dict[str, Any]],
        model: str = "gpt-4o",
        *,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, str]] = None,
        seed: Optional[int] = None,
        user: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, AsyncIterator[ChatCompletionChunk]]:
        """Create a chat completion (async)"""
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if stop is not None:
            payload["stop"] = stop
        if stream:
            payload["stream"] = True
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        if response_format is not None:
            payload["response_format"] = response_format
        if seed is not None:
            payload["seed"] = seed
        if user is not None:
            payload["user"] = user

        payload.update(kwargs)

        if stream:
            return self._stream(payload)

        response = await self._client._request("POST", "/chat/completions", json=payload)
        return ChatCompletion(**response)

    async def _stream(self, payload: Dict[str, Any]) -> AsyncIterator[ChatCompletionChunk]:
        """Stream chat completion chunks (async)"""
        response = await self._client._request("POST", "/chat/completions", json=payload, stream=True)

        async for line in response:
            if isinstance(line, bytes):
                line = line.decode("utf-8")
            line = line.strip()
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    yield ChatCompletionChunk(**chunk)
                except json.JSONDecodeError:
                    continue


class ChatResource:
    """Chat resource with completions"""

    def __init__(self, client: "Client"):
        self.completions = Completions(client)


class AsyncChatResource:
    """Async chat resource with completions"""

    def __init__(self, client: "AsyncClient"):
        self.completions = AsyncCompletions(client)

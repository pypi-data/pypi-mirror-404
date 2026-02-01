"""
Xeno AI SDK - Access 100+ AI models with a single API

Usage:
    import xeno

    client = xeno.Client(api_key="your-api-key")

    # Generate an image
    image = client.image.generate(
        model="flux-pro-1.1",
        prompt="A futuristic cityscape at sunset"
    )
    print(image.url)

    # Chat completion
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)
"""

from xeno.client import Client, AsyncClient
from xeno.exceptions import (
    XenoError,
    AuthenticationError,
    RateLimitError,
    APIError,
    InvalidRequestError,
)
from xeno._types.responses import (
    ImageResponse,
    VideoResponse,
    MusicResponse,
    ChatCompletion,
    ChatCompletionChunk,
)

__version__ = "0.1.0"
__all__ = [
    "Client",
    "AsyncClient",
    "XenoError",
    "AuthenticationError",
    "RateLimitError",
    "APIError",
    "InvalidRequestError",
    "ImageResponse",
    "VideoResponse",
    "MusicResponse",
    "ChatCompletion",
    "ChatCompletionChunk",
]

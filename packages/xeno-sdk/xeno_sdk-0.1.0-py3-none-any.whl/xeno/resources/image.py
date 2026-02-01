"""Image generation resource"""

from typing import Optional, List, Literal, TYPE_CHECKING, Any, Dict
from xeno._types.responses import ImageResponse

if TYPE_CHECKING:
    from xeno.client import Client, AsyncClient


class ImageResource:
    """
    Image generation resource.

    Usage:
        image = client.image.generate(
            model="flux-pro-1.1",
            prompt="A futuristic cityscape at sunset"
        )
        print(image.url)
    """

    def __init__(self, client: "Client"):
        self._client = client

    def generate(
        self,
        prompt: str,
        model: str = "flux-pro-1.1",
        *,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None,
        n: int = 1,
        response_format: Literal["url", "b64_json"] = "url",
        **kwargs: Any,
    ) -> ImageResponse:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of the desired image
            model: Model to use (flux-pro-1.1, flux-kontext, dall-e-3, etc.)
            negative_prompt: What to avoid in the image
            width: Image width in pixels
            height: Image height in pixels
            steps: Number of inference steps
            guidance_scale: How closely to follow the prompt
            seed: Random seed for reproducibility
            n: Number of images to generate
            response_format: Return URL or base64 encoded image

        Returns:
            ImageResponse with generated image(s)
        """
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": f"{width}x{height}",
            "response_format": response_format,
        }

        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if steps:
            payload["steps"] = steps
        if guidance_scale:
            payload["guidance_scale"] = guidance_scale
        if seed is not None:
            payload["seed"] = seed

        payload.update(kwargs)

        response = self._client._request("POST", "/images/generations", json=payload)
        return ImageResponse(model=model, **response)

    def edit(
        self,
        image: str,
        prompt: str,
        model: str = "flux-kontext",
        *,
        mask: Optional[str] = None,
        n: int = 1,
        **kwargs: Any,
    ) -> ImageResponse:
        """
        Edit an existing image based on a prompt.

        Args:
            image: URL or base64 of the image to edit
            prompt: Description of the edit to make
            model: Model to use for editing
            mask: Optional mask indicating areas to edit
            n: Number of variations to generate

        Returns:
            ImageResponse with edited image(s)
        """
        payload: Dict[str, Any] = {
            "model": model,
            "image": image,
            "prompt": prompt,
            "n": n,
        }

        if mask:
            payload["mask"] = mask

        payload.update(kwargs)

        response = self._client._request("POST", "/images/edits", json=payload)
        return ImageResponse(model=model, **response)

    def variations(
        self,
        image: str,
        model: str = "flux-pro-1.1",
        *,
        n: int = 1,
        **kwargs: Any,
    ) -> ImageResponse:
        """
        Generate variations of an existing image.

        Args:
            image: URL or base64 of the source image
            model: Model to use
            n: Number of variations to generate

        Returns:
            ImageResponse with image variations
        """
        payload: Dict[str, Any] = {
            "model": model,
            "image": image,
            "n": n,
        }
        payload.update(kwargs)

        response = self._client._request("POST", "/images/variations", json=payload)
        return ImageResponse(model=model, **response)


class AsyncImageResource:
    """Async image generation resource"""

    def __init__(self, client: "AsyncClient"):
        self._client = client

    async def generate(
        self,
        prompt: str,
        model: str = "flux-pro-1.1",
        *,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None,
        n: int = 1,
        response_format: Literal["url", "b64_json"] = "url",
        **kwargs: Any,
    ) -> ImageResponse:
        """Generate an image from a text prompt (async)"""
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": f"{width}x{height}",
            "response_format": response_format,
        }

        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if steps:
            payload["steps"] = steps
        if guidance_scale:
            payload["guidance_scale"] = guidance_scale
        if seed is not None:
            payload["seed"] = seed

        payload.update(kwargs)

        response = await self._client._request("POST", "/images/generations", json=payload)
        return ImageResponse(model=model, **response)

    async def edit(
        self,
        image: str,
        prompt: str,
        model: str = "flux-kontext",
        *,
        mask: Optional[str] = None,
        n: int = 1,
        **kwargs: Any,
    ) -> ImageResponse:
        """Edit an existing image (async)"""
        payload: Dict[str, Any] = {
            "model": model,
            "image": image,
            "prompt": prompt,
            "n": n,
        }

        if mask:
            payload["mask"] = mask

        payload.update(kwargs)

        response = await self._client._request("POST", "/images/edits", json=payload)
        return ImageResponse(model=model, **response)

    async def variations(
        self,
        image: str,
        model: str = "flux-pro-1.1",
        *,
        n: int = 1,
        **kwargs: Any,
    ) -> ImageResponse:
        """Generate variations of an image (async)"""
        payload: Dict[str, Any] = {
            "model": model,
            "image": image,
            "n": n,
        }
        payload.update(kwargs)

        response = await self._client._request("POST", "/images/variations", json=payload)
        return ImageResponse(model=model, **response)

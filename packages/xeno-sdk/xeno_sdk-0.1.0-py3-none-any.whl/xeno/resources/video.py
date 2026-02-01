"""Video generation resource"""

from typing import Optional, Literal, TYPE_CHECKING, Any, Dict
import time
from xeno._types.responses import VideoResponse

if TYPE_CHECKING:
    from xeno.client import Client, AsyncClient


class VideoResource:
    """
    Video generation resource.

    Usage:
        video = client.video.generate(
            model="veo-3.1",
            prompt="A drone shot flying over mountains"
        )
        print(video.url)
    """

    def __init__(self, client: "Client"):
        self._client = client

    def generate(
        self,
        prompt: str,
        model: str = "veo-3.1",
        *,
        image: Optional[str] = None,
        duration: int = 5,
        resolution: Literal["480p", "720p", "1080p", "4k"] = "1080p",
        fps: int = 24,
        aspect_ratio: Optional[str] = None,
        seed: Optional[int] = None,
        wait: bool = True,
        poll_interval: float = 2.0,
        **kwargs: Any,
    ) -> VideoResponse:
        """
        Generate a video from a text prompt.

        Args:
            prompt: Text description of the desired video
            model: Model to use (veo-3.1, runway-aleph, minimax-video-01, etc.)
            image: Optional starting image for img2vid
            duration: Video duration in seconds
            resolution: Output resolution
            fps: Frames per second
            aspect_ratio: Aspect ratio (e.g., "16:9", "9:16")
            seed: Random seed for reproducibility
            wait: If True, wait for video to complete before returning
            poll_interval: How often to poll for completion (seconds)

        Returns:
            VideoResponse with generated video
        """
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "fps": fps,
        }

        if image:
            payload["image"] = image
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if seed is not None:
            payload["seed"] = seed

        payload.update(kwargs)

        response = self._client._request("POST", "/video/generations", json=payload)
        result = VideoResponse(model=model, **response)

        if wait and result.status in ("pending", "processing"):
            result = self._wait_for_completion(result.id, poll_interval)

        return result

    def get(self, video_id: str) -> VideoResponse:
        """
        Get the status of a video generation.

        Args:
            video_id: The ID of the video generation

        Returns:
            VideoResponse with current status
        """
        response = self._client._request("GET", f"/video/generations/{video_id}")
        return VideoResponse(**response)

    def _wait_for_completion(
        self, video_id: str, poll_interval: float = 2.0
    ) -> VideoResponse:
        """Wait for video generation to complete"""
        while True:
            result = self.get(video_id)
            if result.status in ("completed", "failed"):
                return result
            time.sleep(poll_interval)


class AsyncVideoResource:
    """Async video generation resource"""

    def __init__(self, client: "AsyncClient"):
        self._client = client

    async def generate(
        self,
        prompt: str,
        model: str = "veo-3.1",
        *,
        image: Optional[str] = None,
        duration: int = 5,
        resolution: Literal["480p", "720p", "1080p", "4k"] = "1080p",
        fps: int = 24,
        aspect_ratio: Optional[str] = None,
        seed: Optional[int] = None,
        wait: bool = True,
        poll_interval: float = 2.0,
        **kwargs: Any,
    ) -> VideoResponse:
        """Generate a video from a text prompt (async)"""
        import asyncio

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "fps": fps,
        }

        if image:
            payload["image"] = image
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if seed is not None:
            payload["seed"] = seed

        payload.update(kwargs)

        response = await self._client._request("POST", "/video/generations", json=payload)
        result = VideoResponse(model=model, **response)

        if wait and result.status in ("pending", "processing"):
            result = await self._wait_for_completion(result.id, poll_interval)

        return result

    async def get(self, video_id: str) -> VideoResponse:
        """Get the status of a video generation (async)"""
        response = await self._client._request("GET", f"/video/generations/{video_id}")
        return VideoResponse(**response)

    async def _wait_for_completion(
        self, video_id: str, poll_interval: float = 2.0
    ) -> VideoResponse:
        """Wait for video generation to complete (async)"""
        import asyncio

        while True:
            result = await self.get(video_id)
            if result.status in ("completed", "failed"):
                return result
            await asyncio.sleep(poll_interval)

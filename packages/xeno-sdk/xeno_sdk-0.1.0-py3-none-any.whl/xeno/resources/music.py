"""Music generation resource"""

from typing import Optional, List, Literal, TYPE_CHECKING, Any, Dict
import time
from xeno._types.responses import MusicResponse

if TYPE_CHECKING:
    from xeno.client import Client, AsyncClient


class MusicResource:
    """
    Music generation resource.

    Usage:
        music = client.music.generate(
            model="suno-v4",
            prompt="An upbeat electronic track with synths"
        )
        print(music.url)
    """

    def __init__(self, client: "Client"):
        self._client = client

    def generate(
        self,
        prompt: str,
        model: str = "suno-v4",
        *,
        duration: int = 120,
        genre: Optional[str] = None,
        mood: Optional[str] = None,
        tempo: Optional[int] = None,
        lyrics: Optional[str] = None,
        instrumental: bool = False,
        seed: Optional[int] = None,
        wait: bool = True,
        poll_interval: float = 3.0,
        **kwargs: Any,
    ) -> MusicResponse:
        """
        Generate a music track from a text prompt.

        Args:
            prompt: Text description of the desired music
            model: Model to use (suno-v4, suno-v3.5, udio)
            duration: Track duration in seconds
            genre: Music genre (e.g., "electronic", "rock", "jazz")
            mood: Mood of the track (e.g., "happy", "melancholic")
            tempo: BPM (beats per minute)
            lyrics: Custom lyrics for the track
            instrumental: If True, generate instrumental only
            seed: Random seed for reproducibility
            wait: If True, wait for generation to complete
            poll_interval: How often to poll for completion (seconds)

        Returns:
            MusicResponse with generated track
        """
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "instrumental": instrumental,
        }

        if genre:
            payload["genre"] = genre
        if mood:
            payload["mood"] = mood
        if tempo:
            payload["tempo"] = tempo
        if lyrics:
            payload["lyrics"] = lyrics
        if seed is not None:
            payload["seed"] = seed

        payload.update(kwargs)

        response = self._client._request("POST", "/music/generations", json=payload)
        result = MusicResponse(model=model, **response)

        if wait and result.status in ("pending", "processing"):
            result = self._wait_for_completion(result.id, poll_interval)

        return result

    def get(self, music_id: str) -> MusicResponse:
        """
        Get the status of a music generation.

        Args:
            music_id: The ID of the music generation

        Returns:
            MusicResponse with current status
        """
        response = self._client._request("GET", f"/music/generations/{music_id}")
        return MusicResponse(**response)

    def _wait_for_completion(
        self, music_id: str, poll_interval: float = 3.0
    ) -> MusicResponse:
        """Wait for music generation to complete"""
        while True:
            result = self.get(music_id)
            if result.status in ("completed", "failed"):
                return result
            time.sleep(poll_interval)


class AsyncMusicResource:
    """Async music generation resource"""

    def __init__(self, client: "AsyncClient"):
        self._client = client

    async def generate(
        self,
        prompt: str,
        model: str = "suno-v4",
        *,
        duration: int = 120,
        genre: Optional[str] = None,
        mood: Optional[str] = None,
        tempo: Optional[int] = None,
        lyrics: Optional[str] = None,
        instrumental: bool = False,
        seed: Optional[int] = None,
        wait: bool = True,
        poll_interval: float = 3.0,
        **kwargs: Any,
    ) -> MusicResponse:
        """Generate a music track from a text prompt (async)"""
        import asyncio

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "instrumental": instrumental,
        }

        if genre:
            payload["genre"] = genre
        if mood:
            payload["mood"] = mood
        if tempo:
            payload["tempo"] = tempo
        if lyrics:
            payload["lyrics"] = lyrics
        if seed is not None:
            payload["seed"] = seed

        payload.update(kwargs)

        response = await self._client._request("POST", "/music/generations", json=payload)
        result = MusicResponse(model=model, **response)

        if wait and result.status in ("pending", "processing"):
            result = await self._wait_for_completion(result.id, poll_interval)

        return result

    async def get(self, music_id: str) -> MusicResponse:
        """Get the status of a music generation (async)"""
        response = await self._client._request("GET", f"/music/generations/{music_id}")
        return MusicResponse(**response)

    async def _wait_for_completion(
        self, music_id: str, poll_interval: float = 3.0
    ) -> MusicResponse:
        """Wait for music generation to complete (async)"""
        import asyncio

        while True:
            result = await self.get(music_id)
            if result.status in ("completed", "failed"):
                return result
            await asyncio.sleep(poll_interval)

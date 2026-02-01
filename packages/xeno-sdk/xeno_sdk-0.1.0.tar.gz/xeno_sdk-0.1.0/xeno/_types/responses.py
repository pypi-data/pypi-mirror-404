"""Type definitions for Xeno SDK responses"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============== Image Types ==============

class ImageData(BaseModel):
    """Individual image in a response"""
    url: Optional[str] = None
    b64_json: Optional[str] = None
    revised_prompt: Optional[str] = None


class ImageResponse(BaseModel):
    """Response from image generation"""
    created: int
    data: List[ImageData]
    model: str

    @property
    def url(self) -> Optional[str]:
        """Convenience property to get first image URL"""
        if self.data and len(self.data) > 0:
            return self.data[0].url
        return None

    @property
    def urls(self) -> List[str]:
        """Get all image URLs"""
        return [img.url for img in self.data if img.url]


# ============== Video Types ==============

class VideoData(BaseModel):
    """Individual video in a response"""
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[float] = None
    status: Optional[str] = None


class VideoResponse(BaseModel):
    """Response from video generation"""
    id: str
    status: Literal["pending", "processing", "completed", "failed"]
    created: int
    data: Optional[List[VideoData]] = None
    model: str
    error: Optional[str] = None

    @property
    def url(self) -> Optional[str]:
        """Convenience property to get first video URL"""
        if self.data and len(self.data) > 0:
            return self.data[0].url
        return None

    @property
    def is_complete(self) -> bool:
        """Check if video generation is complete"""
        return self.status == "completed"


# ============== Music Types ==============

class MusicData(BaseModel):
    """Individual music track in a response"""
    url: Optional[str] = None
    duration: Optional[float] = None
    title: Optional[str] = None
    tags: Optional[List[str]] = None


class MusicResponse(BaseModel):
    """Response from music generation"""
    id: str
    status: Literal["pending", "processing", "completed", "failed"]
    created: int
    data: Optional[List[MusicData]] = None
    model: str
    error: Optional[str] = None

    @property
    def url(self) -> Optional[str]:
        """Convenience property to get first track URL"""
        if self.data and len(self.data) > 0:
            return self.data[0].url
        return None


# ============== Chat Types ==============

class FunctionCall(BaseModel):
    """Function call in a message"""
    name: str
    arguments: str


class ToolCall(BaseModel):
    """Tool call in a message"""
    id: str
    type: Literal["function"]
    function: FunctionCall


class ChatMessage(BaseModel):
    """A chat message"""
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None


class Choice(BaseModel):
    """A completion choice"""
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


class Usage(BaseModel):
    """Token usage information"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletion(BaseModel):
    """Chat completion response"""
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Optional[Usage] = None


class DeltaMessage(BaseModel):
    """Delta message for streaming"""
    role: Optional[str] = None
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


class StreamChoice(BaseModel):
    """A streaming choice"""
    index: int
    delta: DeltaMessage
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    """Streaming chat completion chunk"""
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: List[StreamChoice]


# ============== Model Types ==============

class Model(BaseModel):
    """Model information"""
    id: str
    object: Literal["model"] = "model"
    created: int
    owned_by: str


class ModelList(BaseModel):
    """List of models"""
    object: Literal["list"] = "list"
    data: List[Model]

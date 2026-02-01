"""Voice-related models for the HeyGen API."""

from typing import List, Optional

from pydantic import BaseModel

from .base import BaseHeyGenResponse


class VoiceInfo(BaseModel):
    """Information about an available voice."""

    voice_id: str
    language: str
    gender: str
    name: str
    preview_audio: Optional[str] = None  # Some voices have empty preview_audio
    support_pause: bool
    emotion_support: bool
    support_interactive_avatar: bool


class VoicesData(BaseModel):
    """Container for voice list from API."""

    voices: List[VoiceInfo]


class VoicesResponse(BaseHeyGenResponse):
    """API response for voices endpoint."""

    data: Optional[VoicesData] = None


class MCPVoicesResponse(BaseHeyGenResponse):
    """MCP response wrapper for voices."""

    voices: Optional[List[VoiceInfo]] = None

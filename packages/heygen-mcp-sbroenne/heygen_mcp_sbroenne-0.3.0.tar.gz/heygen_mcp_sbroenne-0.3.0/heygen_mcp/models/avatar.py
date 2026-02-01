"""Avatar-related models for the HeyGen API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .base import BaseHeyGenResponse


class Avatar(BaseModel):
    """Avatar model matching HeyGen API response for avatar groups."""

    id: str = Field(alias="id")
    name: str = Field(alias="name")
    gender: Optional[str] = None
    preview_image_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    premium: Optional[bool] = None
    type: Optional[str] = None
    tags: Optional[List[str]] = None
    default_voice_id: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    train_status: Optional[str] = None
    moderation_msg: Optional[str] = None

    @property
    def avatar_id(self) -> str:
        """Backwards-compatible access to id."""
        return self.id

    @property
    def avatar_name(self) -> str:
        """Backwards-compatible access to name."""
        return self.name

    model_config = {"populate_by_name": True}


class AvatarV2(BaseModel):
    """Avatar model from List All Avatars (V2) endpoint."""

    avatar_id: str
    avatar_name: str
    gender: Optional[str] = None
    preview_image_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    premium: Optional[bool] = None
    type: Optional[str] = None
    tags: Optional[List[str]] = None

    model_config = {"extra": "ignore"}


class AvatarDetails(BaseModel):
    """Detailed avatar information."""

    avatar_id: Optional[str] = Field(default=None, alias="id")
    avatar_name: Optional[str] = Field(default=None, alias="name")
    type: Optional[str] = None
    gender: Optional[str] = None
    preview_image_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    premium: Optional[bool] = None
    tags: Optional[List[str]] = None
    poses: Optional[List[Dict[str, Any]]] = None
    voices: Optional[List[Dict[str, Any]]] = None
    looks: Optional[List[Dict[str, Any]]] = None

    model_config = {"extra": "ignore", "populate_by_name": True}


class AvatarsInGroupData(BaseModel):
    """Container for avatars in a group."""

    avatar_list: List[Avatar]


class AvatarsInGroupResponse(BaseHeyGenResponse):
    """API response for avatars in a group."""

    data: Optional[AvatarsInGroupData] = None


class AvatarsV2Data(BaseModel):
    """Container for V2 avatar list."""

    avatars: List[AvatarV2]


class AvatarsV2Response(BaseHeyGenResponse):
    """API response for list all avatars V2."""

    data: Optional[AvatarsV2Data] = None


class AvatarDetailsResponse(BaseHeyGenResponse):
    """API response for avatar details."""

    data: Optional[AvatarDetails] = None


class MCPAvatarsInGroupResponse(BaseHeyGenResponse):
    """MCP response wrapper for avatars in a group."""

    avatars: Optional[List[Avatar]] = None


class MCPListAvatarsResponse(BaseHeyGenResponse):
    """MCP response wrapper for list all avatars."""

    avatars: Optional[List[AvatarV2]] = None
    total_count: Optional[int] = None


class MCPAvatarDetailsResponse(BaseHeyGenResponse):
    """MCP response wrapper for avatar details."""

    avatar: Optional[AvatarDetails] = None

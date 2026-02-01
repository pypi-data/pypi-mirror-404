"""Avatar group models for the HeyGen API."""

from typing import List, Optional

from pydantic import BaseModel, HttpUrl

from .base import BaseHeyGenResponse


class AvatarGroup(BaseModel):
    """Information about an avatar group."""

    id: str
    name: str
    created_at: int
    num_looks: int
    preview_image: HttpUrl
    group_type: str
    train_status: Optional[str] = None


class AvatarGroupListData(BaseModel):
    """Container for avatar group list."""

    total_count: int
    avatar_group_list: List[AvatarGroup]


class AvatarGroupListResponse(BaseHeyGenResponse):
    """API response for avatar group list."""

    data: Optional[AvatarGroupListData] = None


class MCPAvatarGroupResponse(BaseHeyGenResponse):
    """MCP response wrapper for avatar groups."""

    avatar_groups: Optional[List[AvatarGroup]] = None
    total_count: Optional[int] = None

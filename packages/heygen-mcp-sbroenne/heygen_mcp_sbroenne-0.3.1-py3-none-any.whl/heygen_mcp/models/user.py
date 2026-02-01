"""User-related models for the HeyGen API."""

from typing import Optional

from pydantic import BaseModel

from .base import BaseHeyGenResponse


class QuotaDetails(BaseModel):
    """Quota details from API.

    Fields are optional as API may return different fields.
    """

    api: Optional[int] = None
    streaming_avatar: Optional[int] = None
    streaming_avatar_instance_quota: Optional[int] = None
    seat: Optional[int] = None
    avatar_ivi: Optional[int] = None
    personalized_video_ivi: Optional[int] = None
    plan_credit: Optional[int] = None

    model_config = {"extra": "ignore"}


class RemainingQuota(BaseModel):
    """Remaining quota information."""

    remaining_quota: int
    details: QuotaDetails


class RemainingQuotaResponse(BaseHeyGenResponse):
    """API response for remaining quota."""

    data: Optional[RemainingQuota] = None


class UserInfo(BaseModel):
    """User profile information."""

    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    model_config = {"extra": "ignore"}


class UserInfoData(BaseModel):
    """Container for user info."""

    user: UserInfo

    model_config = {"extra": "ignore"}


class UserInfoResponse(BaseModel):
    """API response for user info (v1 endpoint)."""

    code: Optional[int] = None
    data: Optional[UserInfo] = None
    message: Optional[str] = None


class MCPGetCreditsResponse(BaseHeyGenResponse):
    """MCP response wrapper for remaining credits."""

    remaining_credits: Optional[int] = None


class MCPUserInfoResponse(BaseHeyGenResponse):
    """MCP response wrapper for user info."""

    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

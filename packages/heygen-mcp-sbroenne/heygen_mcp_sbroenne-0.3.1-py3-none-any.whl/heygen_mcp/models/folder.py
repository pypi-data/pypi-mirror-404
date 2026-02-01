"""Folder models for the HeyGen API."""

from typing import List, Optional

from pydantic import BaseModel

from .base import BaseHeyGenResponse


class Folder(BaseModel):
    """Folder information from HeyGen API."""

    id: str
    name: str
    parent_id: Optional[str] = None
    project_type: Optional[str] = None
    is_trash: bool = False
    created_ts: Optional[int] = None
    updated_ts: Optional[int] = None
    direct_children_count: Optional[int] = None
    creator_username: Optional[str] = None


class FolderListData(BaseModel):
    """Data structure for folder list response."""

    folders: List[Folder]
    token: Optional[str] = None
    total: int


class FolderListResponse(BaseHeyGenResponse):
    """API response for listing folders."""

    data: Optional[FolderListData] = None


class FolderCreateResponse(BaseHeyGenResponse):
    """API response for creating a folder."""

    data: Optional[Folder] = None


class FolderUpdateResponse(BaseHeyGenResponse):
    """API response for updating a folder."""

    data: Optional[Folder] = None


class FolderTrashRestoreResponse(BaseHeyGenResponse):
    """API response for trash/restore folder operations."""

    data: Optional[dict] = None


# MCP Response Models


class MCPFolderListResponse(BaseHeyGenResponse):
    """MCP response wrapper for listing folders."""

    folders: Optional[List[Folder]] = None
    total: Optional[int] = None
    token: Optional[str] = None


class MCPFolderCreateResponse(BaseHeyGenResponse):
    """MCP response wrapper for creating a folder."""

    folder_id: Optional[str] = None


class MCPFolderUpdateResponse(BaseHeyGenResponse):
    """MCP response wrapper for updating a folder."""

    folder_id: Optional[str] = None
    success: bool = False


class MCPFolderTrashResponse(BaseHeyGenResponse):
    """MCP response wrapper for trashing a folder."""

    folder_id: Optional[str] = None
    success: bool = False


class MCPFolderRestoreResponse(BaseHeyGenResponse):
    """MCP response wrapper for restoring a folder."""

    folder_id: Optional[str] = None
    success: bool = False

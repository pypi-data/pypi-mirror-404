"""Template models for the HeyGen API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .base import BaseHeyGenResponse


class Template(BaseModel):
    """Basic template information."""

    template_id: str
    name: str
    thumbnail_image_url: Optional[str] = None

    model_config = {"extra": "ignore"}


class TemplateVariable(BaseModel):
    """Variable available for replacement in a template."""

    name: str
    type: str
    properties: Optional[Dict[str, Any]] = None

    model_config = {"extra": "ignore"}


class TemplateScene(BaseModel):
    """Scene in a template with its variables."""

    scene_id: Optional[str] = None
    variables: Optional[List[TemplateVariable]] = None

    model_config = {"extra": "ignore"}


class TemplateDetails(BaseModel):
    """Detailed template information including variables."""

    template_id: Optional[str] = Field(default=None, alias="id")
    name: Optional[str] = None
    thumbnail_image_url: Optional[str] = None
    variables: Optional[List[TemplateVariable]] = None
    scenes: Optional[List[TemplateScene]] = None

    model_config = {"extra": "ignore", "populate_by_name": True}


class TemplatesData(BaseModel):
    """Container for template list."""

    templates: List[Template]


class TemplatesResponse(BaseHeyGenResponse):
    """API response for templates list."""

    data: Optional[TemplatesData] = None


class TemplateDetailsResponse(BaseHeyGenResponse):
    """API response for template details (V3)."""

    data: Optional[TemplateDetails] = None


class TemplateVideoGenerateRequest(BaseModel):
    """Request to generate video from template."""

    test: bool = False
    caption: bool = False
    title: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None

    model_config = {"extra": "ignore"}


class TemplateVideoGenerateData(BaseModel):
    """Response data for template video generation."""

    video_id: str

    model_config = {"extra": "ignore"}


class TemplateVideoGenerateResponse(BaseHeyGenResponse):
    """API response for template video generation."""

    data: Optional[TemplateVideoGenerateData] = None


class MCPListTemplatesResponse(BaseHeyGenResponse):
    """MCP response wrapper for templates list."""

    templates: Optional[List[Template]] = None
    total_count: Optional[int] = None


class MCPTemplateDetailsResponse(BaseHeyGenResponse):
    """MCP response wrapper for template details."""

    template: Optional[TemplateDetails] = None


class MCPTemplateVideoGenerateResponse(BaseHeyGenResponse):
    """MCP response wrapper for template video generation."""

    video_id: Optional[str] = None

"""Base model classes for HeyGen API responses."""

from typing import Optional

from pydantic import BaseModel


class BaseHeyGenResponse(BaseModel):
    """Base response model with common error handling."""

    error: Optional[str] = None

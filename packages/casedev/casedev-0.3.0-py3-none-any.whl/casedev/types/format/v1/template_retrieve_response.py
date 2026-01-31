# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["TemplateRetrieveResponse"]


class TemplateRetrieveResponse(BaseModel):
    id: Optional[str] = None
    """Unique template identifier"""

    content: Optional[object] = None
    """Template formatting rules and structure"""

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)
    """Template creation timestamp"""

    description: Optional[str] = None
    """Template description"""

    name: Optional[str] = None
    """Template name"""

    organization_id: Optional[str] = FieldInfo(alias="organizationId", default=None)
    """Organization ID that owns the template"""

    updated_at: Optional[datetime] = FieldInfo(alias="updatedAt", default=None)
    """Template last modification timestamp"""

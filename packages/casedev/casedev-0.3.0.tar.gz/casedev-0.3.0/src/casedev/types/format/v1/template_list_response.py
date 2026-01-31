# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["TemplateListResponse", "Template"]


class Template(BaseModel):
    id: Optional[str] = None
    """Unique template identifier"""

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)
    """Template creation timestamp"""

    description: Optional[str] = None
    """Template description"""

    name: Optional[str] = None
    """Template name"""

    tags: Optional[List[object]] = None
    """Template tags for organization"""

    type: Optional[str] = None
    """Template type/category"""

    usage_count: Optional[int] = FieldInfo(alias="usageCount", default=None)
    """Number of times template has been used"""

    variables: Optional[List[object]] = None
    """Template variables for customization"""


class TemplateListResponse(BaseModel):
    templates: Optional[List[Template]] = None

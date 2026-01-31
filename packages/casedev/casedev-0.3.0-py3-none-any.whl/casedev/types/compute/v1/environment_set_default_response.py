# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["EnvironmentSetDefaultResponse"]


class EnvironmentSetDefaultResponse(BaseModel):
    id: Optional[str] = None
    """Unique environment identifier"""

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)
    """Environment creation timestamp"""

    domain: Optional[str] = None
    """Environment domain"""

    is_default: Optional[bool] = FieldInfo(alias="isDefault", default=None)
    """Whether this is the default environment"""

    name: Optional[str] = None
    """Environment name"""

    slug: Optional[str] = None
    """URL-friendly environment identifier"""

    status: Optional[str] = None
    """Current environment status"""

    updated_at: Optional[datetime] = FieldInfo(alias="updatedAt", default=None)
    """Last update timestamp"""

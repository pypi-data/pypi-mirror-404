# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["EnvironmentListResponse", "Environment"]


class Environment(BaseModel):
    id: Optional[str] = None
    """Unique environment identifier"""

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)
    """Environment creation timestamp"""

    domain: Optional[str] = None
    """Environment domain"""

    is_default: Optional[bool] = FieldInfo(alias="isDefault", default=None)
    """Whether this is the default environment"""

    name: Optional[str] = None
    """Human-readable environment name"""

    slug: Optional[str] = None
    """URL-safe environment identifier"""

    status: Optional[str] = None
    """Environment status"""

    updated_at: Optional[datetime] = FieldInfo(alias="updatedAt", default=None)
    """Last update timestamp"""


class EnvironmentListResponse(BaseModel):
    environments: Optional[List[Environment]] = None

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["SecretListResponse", "Group"]


class Group(BaseModel):
    id: Optional[str] = None
    """Unique identifier for the secret group"""

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)
    """When the secret group was created"""

    description: Optional[str] = None
    """Description of the secret group"""

    name: Optional[str] = None
    """Name of the secret group"""

    updated_at: Optional[datetime] = FieldInfo(alias="updatedAt", default=None)
    """When the secret group was last updated"""


class SecretListResponse(BaseModel):
    groups: Optional[List[Group]] = None

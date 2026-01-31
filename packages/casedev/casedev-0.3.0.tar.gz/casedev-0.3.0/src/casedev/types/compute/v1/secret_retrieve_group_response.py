# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["SecretRetrieveGroupResponse", "Group", "Key"]


class Group(BaseModel):
    id: Optional[str] = None
    """Unique identifier of the secret group"""

    description: Optional[str] = None
    """Description of the secret group"""

    name: Optional[str] = None
    """Name of the secret group"""


class Key(BaseModel):
    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)
    """When the secret was created"""

    key: Optional[str] = None
    """Name of the secret key"""

    updated_at: Optional[datetime] = FieldInfo(alias="updatedAt", default=None)
    """When the secret was last updated"""


class SecretRetrieveGroupResponse(BaseModel):
    group: Optional[Group] = None

    keys: Optional[List[Key]] = None

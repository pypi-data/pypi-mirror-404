# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ...._models import BaseModel

__all__ = ["SecretUpdateGroupResponse"]


class SecretUpdateGroupResponse(BaseModel):
    created: Optional[float] = None
    """Number of new secrets created"""

    group: Optional[str] = None
    """Name of the secret group"""

    message: Optional[str] = None

    success: Optional[bool] = None

    updated: Optional[float] = None
    """Number of existing secrets updated"""

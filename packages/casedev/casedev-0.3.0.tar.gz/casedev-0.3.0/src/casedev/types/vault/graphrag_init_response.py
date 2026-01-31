# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["GraphragInitResponse"]


class GraphragInitResponse(BaseModel):
    message: Optional[str] = None

    status: Optional[str] = None

    success: Optional[bool] = None

    vault_id: Optional[str] = None

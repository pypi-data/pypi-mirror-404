# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["V1RetrieveResponse"]


class V1RetrieveResponse(BaseModel):
    id: str
    """OCR job ID"""

    created_at: datetime
    """Job creation timestamp"""

    status: Literal["pending", "processing", "completed", "failed"]
    """Current job status"""

    completed_at: Optional[datetime] = None
    """Job completion timestamp"""

    metadata: Optional[object] = None
    """Additional processing metadata"""

    page_count: Optional[int] = None
    """Number of pages processed"""

    text: Optional[str] = None
    """Extracted text content (when completed)"""

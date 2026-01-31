# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["GraphragGetStatsResponse"]


class GraphragGetStatsResponse(BaseModel):
    communities: Optional[int] = None
    """Number of entity communities identified"""

    documents: Optional[int] = None
    """Number of processed documents"""

    entities: Optional[int] = None
    """Total number of entities extracted from documents"""

    last_processed: Optional[datetime] = FieldInfo(alias="lastProcessed", default=None)
    """Timestamp of last GraphRAG processing"""

    relationships: Optional[int] = None
    """Total number of relationships between entities"""

    status: Optional[Literal["processing", "completed", "error"]] = None
    """Current processing status"""

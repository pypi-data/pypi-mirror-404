# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ObjectListResponse", "Object"]


class Object(BaseModel):
    id: str
    """Unique object identifier"""

    content_type: str = FieldInfo(alias="contentType")
    """MIME type of the document"""

    created_at: datetime = FieldInfo(alias="createdAt")
    """Document upload timestamp"""

    filename: str
    """Original filename of the uploaded document"""

    ingestion_status: str = FieldInfo(alias="ingestionStatus")
    """Processing status of the document"""

    chunk_count: Optional[float] = FieldInfo(alias="chunkCount", default=None)
    """Number of text chunks created for vectorization"""

    ingestion_completed_at: Optional[datetime] = FieldInfo(alias="ingestionCompletedAt", default=None)
    """Processing completion timestamp"""

    metadata: Optional[object] = None
    """Custom metadata associated with the document"""

    page_count: Optional[float] = FieldInfo(alias="pageCount", default=None)
    """Number of pages in the document"""

    path: Optional[str] = None
    """Optional folder path for hierarchy preservation from source systems"""

    size_bytes: Optional[float] = FieldInfo(alias="sizeBytes", default=None)
    """File size in bytes"""

    tags: Optional[List[str]] = None
    """Custom tags associated with the document"""

    text_length: Optional[float] = FieldInfo(alias="textLength", default=None)
    """Total character count of extracted text"""

    vector_count: Optional[float] = FieldInfo(alias="vectorCount", default=None)
    """Number of vectors generated for semantic search"""


class ObjectListResponse(BaseModel):
    count: float
    """Total number of objects in the vault"""

    objects: List[Object]

    vault_id: str = FieldInfo(alias="vaultId")
    """The ID of the vault"""

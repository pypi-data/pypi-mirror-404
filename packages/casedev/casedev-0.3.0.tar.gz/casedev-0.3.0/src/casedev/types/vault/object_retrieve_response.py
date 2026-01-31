# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ObjectRetrieveResponse"]


class ObjectRetrieveResponse(BaseModel):
    id: str
    """Object ID"""

    content_type: str = FieldInfo(alias="contentType")
    """MIME type"""

    created_at: datetime = FieldInfo(alias="createdAt")
    """Upload timestamp"""

    download_url: str = FieldInfo(alias="downloadUrl")
    """Presigned S3 download URL"""

    expires_in: int = FieldInfo(alias="expiresIn")
    """URL expiration time in seconds"""

    filename: str
    """Original filename"""

    ingestion_status: str = FieldInfo(alias="ingestionStatus")
    """Processing status (pending, processing, completed, failed)"""

    vault_id: str = FieldInfo(alias="vaultId")
    """Vault ID"""

    chunk_count: Optional[int] = FieldInfo(alias="chunkCount", default=None)
    """Number of text chunks created"""

    metadata: Optional[object] = None
    """Additional metadata"""

    page_count: Optional[int] = FieldInfo(alias="pageCount", default=None)
    """Number of pages (for documents)"""

    path: Optional[str] = None
    """Optional folder path for hierarchy preservation"""

    size_bytes: Optional[int] = FieldInfo(alias="sizeBytes", default=None)
    """File size in bytes"""

    text_length: Optional[int] = FieldInfo(alias="textLength", default=None)
    """Length of extracted text"""

    vector_count: Optional[int] = FieldInfo(alias="vectorCount", default=None)
    """Number of embedding vectors generated"""

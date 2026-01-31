# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["VaultCreateResponse"]


class VaultCreateResponse(BaseModel):
    id: Optional[str] = None
    """Unique vault identifier"""

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)
    """Vault creation timestamp"""

    description: Optional[str] = None
    """Vault description"""

    enable_indexing: Optional[bool] = FieldInfo(alias="enableIndexing", default=None)
    """Whether vector indexing is enabled for this vault"""

    files_bucket: Optional[str] = FieldInfo(alias="filesBucket", default=None)
    """S3 bucket name for document storage"""

    index_name: Optional[str] = FieldInfo(alias="indexName", default=None)
    """Vector search index name. Null for storage-only vaults."""

    name: Optional[str] = None
    """Vault display name"""

    region: Optional[str] = None
    """AWS region for storage"""

    vector_bucket: Optional[str] = FieldInfo(alias="vectorBucket", default=None)
    """S3 bucket name for vector embeddings. Null for storage-only vaults."""

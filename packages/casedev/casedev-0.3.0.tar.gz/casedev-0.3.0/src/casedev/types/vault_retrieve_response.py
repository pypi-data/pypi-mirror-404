# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["VaultRetrieveResponse", "ChunkStrategy"]


class ChunkStrategy(BaseModel):
    """Document chunking strategy configuration"""

    chunk_size: Optional[int] = FieldInfo(alias="chunkSize", default=None)
    """Target size for each chunk in tokens"""

    method: Optional[str] = None
    """Chunking method (e.g., 'semantic', 'fixed')"""

    min_chunk_size: Optional[int] = FieldInfo(alias="minChunkSize", default=None)
    """Minimum chunk size in tokens"""

    overlap: Optional[int] = None
    """Number of overlapping tokens between chunks"""


class VaultRetrieveResponse(BaseModel):
    id: str
    """Vault identifier"""

    created_at: datetime = FieldInfo(alias="createdAt")
    """Vault creation timestamp"""

    files_bucket: str = FieldInfo(alias="filesBucket")
    """S3 bucket for document storage"""

    name: str
    """Vault name"""

    region: str
    """AWS region"""

    chunk_strategy: Optional[ChunkStrategy] = FieldInfo(alias="chunkStrategy", default=None)
    """Document chunking strategy configuration"""

    description: Optional[str] = None
    """Vault description"""

    enable_graph: Optional[bool] = FieldInfo(alias="enableGraph", default=None)
    """Whether GraphRAG is enabled"""

    index_name: Optional[str] = FieldInfo(alias="indexName", default=None)
    """Search index name"""

    kms_key_id: Optional[str] = FieldInfo(alias="kmsKeyId", default=None)
    """KMS key for encryption"""

    metadata: Optional[object] = None
    """Additional vault metadata"""

    total_bytes: Optional[int] = FieldInfo(alias="totalBytes", default=None)
    """Total storage size in bytes"""

    total_objects: Optional[int] = FieldInfo(alias="totalObjects", default=None)
    """Number of stored documents"""

    total_vectors: Optional[int] = FieldInfo(alias="totalVectors", default=None)
    """Number of vector embeddings"""

    updated_at: Optional[datetime] = FieldInfo(alias="updatedAt", default=None)
    """Last update timestamp"""

    vector_bucket: Optional[str] = FieldInfo(alias="vectorBucket", default=None)
    """S3 bucket for vector embeddings"""

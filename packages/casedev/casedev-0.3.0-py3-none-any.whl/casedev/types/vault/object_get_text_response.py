# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from ..._models import BaseModel

__all__ = ["ObjectGetTextResponse", "Metadata"]


class Metadata(BaseModel):
    chunk_count: int
    """Number of text chunks the document was split into"""

    filename: str
    """Original filename of the document"""

    length: int
    """Total character count of the extracted text"""

    object_id: str
    """The object ID"""

    vault_id: str
    """The vault ID"""

    ingestion_completed_at: Optional[datetime] = None
    """When the document processing completed"""


class ObjectGetTextResponse(BaseModel):
    metadata: Metadata

    text: str
    """Full concatenated text content from all chunks"""

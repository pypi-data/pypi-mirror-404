# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["VaultSearchResponse", "Chunk", "Source"]


class Chunk(BaseModel):
    chunk_index: Optional[int] = None
    """Index of the chunk within the document (0-based)"""

    distance: Optional[float] = None
    """Vector similarity distance (lower is more similar)"""

    object_id: Optional[str] = None
    """ID of the source document"""

    page_end: Optional[int] = None
    """PDF page number where the chunk ends (1-indexed).

    Null for non-PDF documents or documents ingested before page tracking was added.
    """

    page_start: Optional[int] = None
    """PDF page number where the chunk begins (1-indexed).

    Null for non-PDF documents or documents ingested before page tracking was added.
    """

    score: Optional[float] = None
    """Relevance score (deprecated, use distance or hybridScore)"""

    source: Optional[str] = None
    """Source identifier (deprecated, use object_id)"""

    text: Optional[str] = None
    """Preview of the chunk text (up to 500 characters)"""

    word_end_index: Optional[int] = None
    """Ending word index (0-based) in the OCR word list.

    Use with GET /vault/:id/objects/:objectId/ocr-words to retrieve bounding boxes
    for highlighting.
    """

    word_start_index: Optional[int] = None
    """Starting word index (0-based) in the OCR word list.

    Use with GET /vault/:id/objects/:objectId/ocr-words to retrieve bounding boxes
    for highlighting.
    """


class Source(BaseModel):
    id: Optional[str] = None

    chunk_count: Optional[int] = FieldInfo(alias="chunkCount", default=None)

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)

    filename: Optional[str] = None

    ingestion_completed_at: Optional[datetime] = FieldInfo(alias="ingestionCompletedAt", default=None)

    page_count: Optional[int] = FieldInfo(alias="pageCount", default=None)

    text_length: Optional[int] = FieldInfo(alias="textLength", default=None)


class VaultSearchResponse(BaseModel):
    chunks: Optional[List[Chunk]] = None
    """Relevant text chunks with similarity scores and page locations"""

    method: Optional[str] = None
    """Search method used"""

    query: Optional[str] = None
    """Original search query"""

    response: Optional[str] = None
    """AI-generated answer based on search results (for global/entity methods)"""

    sources: Optional[List[Source]] = None

    vault_id: Optional[str] = None
    """ID of the searched vault"""

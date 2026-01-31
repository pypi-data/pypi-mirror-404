# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["TranscriptionRetrieveResponse"]


class TranscriptionRetrieveResponse(BaseModel):
    id: str
    """Unique transcription job ID"""

    status: Literal["queued", "processing", "completed", "failed"]
    """Current status of the transcription job"""

    audio_duration: Optional[float] = None
    """Duration of the audio file in seconds"""

    confidence: Optional[float] = None
    """Overall confidence score (0-100)"""

    error: Optional[str] = None
    """Error message (only present when status is failed)"""

    result_object_id: Optional[str] = None
    """Result transcript object ID (vault-based jobs, when completed)"""

    source_object_id: Optional[str] = None
    """Source audio object ID (vault-based jobs only)"""

    text: Optional[str] = None
    """Full transcription text (legacy direct URL jobs only)"""

    vault_id: Optional[str] = None
    """Vault ID (vault-based jobs only)"""

    word_count: Optional[int] = None
    """Number of words in the transcript"""

    words: Optional[List[object]] = None
    """Word-level timestamps (legacy direct URL jobs only)"""

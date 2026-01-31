# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["TranscriptionCreateResponse"]


class TranscriptionCreateResponse(BaseModel):
    id: Optional[str] = None
    """Unique transcription job ID"""

    source_object_id: Optional[str] = None
    """Source audio object ID (only for vault-based transcription)"""

    status: Optional[Literal["queued", "processing", "completed", "error"]] = None
    """Current status of the transcription job"""

    vault_id: Optional[str] = None
    """Vault ID (only for vault-based transcription)"""

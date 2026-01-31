# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from ..._models import BaseModel

__all__ = ["V1ListVoicesResponse", "Voice"]


class Voice(BaseModel):
    available_for_tiers: Optional[List[str]] = None
    """Available subscription tiers"""

    category: Optional[str] = None
    """Voice category"""

    description: Optional[str] = None
    """Voice description"""

    labels: Optional[object] = None
    """Voice characteristics and metadata"""

    name: Optional[str] = None
    """Voice name"""

    preview_url: Optional[str] = None
    """URL to preview audio sample"""

    voice_id: Optional[str] = None
    """Unique voice identifier"""


class V1ListVoicesResponse(BaseModel):
    next_page_token: Optional[str] = None
    """Token for next page of results"""

    total_count: Optional[int] = None
    """Total number of voices (if requested)"""

    voices: Optional[List[Voice]] = None

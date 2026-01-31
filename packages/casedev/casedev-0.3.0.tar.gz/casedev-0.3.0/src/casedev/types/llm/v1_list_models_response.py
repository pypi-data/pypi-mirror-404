# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from ..._models import BaseModel

__all__ = ["V1ListModelsResponse", "Data", "DataPricing"]


class DataPricing(BaseModel):
    input: Optional[str] = None
    """Input token price per token"""

    input_cache_read: Optional[str] = None
    """Cache read price per token (if supported)"""

    output: Optional[str] = None
    """Output token price per token"""


class Data(BaseModel):
    id: Optional[str] = None
    """Unique model identifier"""

    created: Optional[int] = None
    """Unix timestamp of model creation"""

    object: Optional[str] = None
    """Object type, always 'model'"""

    owned_by: Optional[str] = None
    """Model provider (openai, anthropic, google, casemark, etc.)"""

    pricing: Optional[DataPricing] = None


class V1ListModelsResponse(BaseModel):
    data: Optional[List[Data]] = None

    object: Optional[str] = None
    """Response object type, always 'list'"""

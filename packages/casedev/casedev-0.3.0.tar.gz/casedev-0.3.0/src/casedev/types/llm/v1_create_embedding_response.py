# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from ..._models import BaseModel

__all__ = ["V1CreateEmbeddingResponse", "Data", "Usage"]


class Data(BaseModel):
    embedding: Optional[List[float]] = None

    index: Optional[int] = None

    object: Optional[str] = None


class Usage(BaseModel):
    prompt_tokens: Optional[int] = None

    total_tokens: Optional[int] = None


class V1CreateEmbeddingResponse(BaseModel):
    data: Optional[List[Data]] = None

    model: Optional[str] = None

    object: Optional[str] = None

    usage: Optional[Usage] = None

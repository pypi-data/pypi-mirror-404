# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["LlmGetConfigResponse", "Model"]


class Model(BaseModel):
    id: str
    """Unique model identifier"""

    api_model_type: str = FieldInfo(alias="modelType")
    """Type of model (e.g., language, embedding)"""

    name: str
    """Human-readable model name"""

    description: Optional[str] = None
    """Model description and capabilities"""

    pricing: Optional[object] = None
    """Pricing information for the model"""

    specification: Optional[object] = None
    """Technical specifications and limits"""


class LlmGetConfigResponse(BaseModel):
    models: List[Model]

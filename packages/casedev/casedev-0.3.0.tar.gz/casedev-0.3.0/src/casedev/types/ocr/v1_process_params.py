# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from typing_extensions import Literal, Required, TypeAlias, TypedDict

__all__ = ["V1ProcessParams", "Features", "FeaturesTables"]


class V1ProcessParams(TypedDict, total=False):
    document_url: Required[str]
    """URL or S3 path to the document to process"""

    callback_url: str
    """URL to receive completion webhook"""

    document_id: str
    """Optional custom document identifier"""

    engine: Literal["doctr", "paddleocr"]
    """OCR engine to use"""

    features: Features
    """Additional processing options"""

    result_bucket: str
    """S3 bucket to store results"""

    result_prefix: str
    """S3 key prefix for results"""


class FeaturesTablesTyped(TypedDict, total=False):
    """Extract tables as structured data"""

    format: Literal["csv", "json"]
    """Output format for extracted tables"""


FeaturesTables: TypeAlias = Union[FeaturesTablesTyped, Dict[str, object]]


class Features(TypedDict, total=False):
    """Additional processing options"""

    embed: Dict[str, object]
    """Generate searchable PDF with text layer"""

    forms: Dict[str, object]
    """Detect and extract form fields"""

    tables: FeaturesTables
    """Extract tables as structured data"""

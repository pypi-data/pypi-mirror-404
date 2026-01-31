# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from typing_extensions import Literal, Required, Annotated, TypeAlias, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["VaultSearchParams", "Filters"]


class VaultSearchParams(TypedDict, total=False):
    query: Required[str]
    """Search query or question to find relevant documents"""

    filters: Filters
    """Filters to narrow search results to specific documents"""

    method: Literal["vector", "graph", "hybrid", "global", "local", "fast", "entity"]
    """
    Search method: 'global' for comprehensive questions, 'entity' for specific
    entities, 'fast' for quick similarity search, 'hybrid' for combined approach
    """

    top_k: Annotated[int, PropertyInfo(alias="topK")]
    """Maximum number of results to return"""


class FiltersTyped(TypedDict, total=False):
    """Filters to narrow search results to specific documents"""

    object_id: Union[str, SequenceNotStr[str]]
    """Filter to specific document(s) by object ID.

    Accepts a single ID or array of IDs.
    """


Filters: TypeAlias = Union[FiltersTyped, Dict[str, object]]

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["VaultCreateParams"]


class VaultCreateParams(TypedDict, total=False):
    name: Required[str]
    """Display name for the vault"""

    description: str
    """Optional description of the vault's purpose"""

    enable_graph: Annotated[bool, PropertyInfo(alias="enableGraph")]
    """Enable knowledge graph for entity relationship mapping.

    Only applies when enableIndexing is true.
    """

    enable_indexing: Annotated[bool, PropertyInfo(alias="enableIndexing")]
    """Enable vector indexing and search capabilities.

    Set to false for storage-only vaults.
    """

    metadata: object
    """
    Optional metadata to attach to the vault (e.g., { containsPHI: true } for HIPAA
    compliance tracking)
    """

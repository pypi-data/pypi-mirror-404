# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["VaultIngestResponse"]


class VaultIngestResponse(BaseModel):
    enable_graph_rag: bool = FieldInfo(alias="enableGraphRAG")
    """
    Always false - GraphRAG must be triggered separately via POST
    /vault/:id/graphrag/:objectId
    """

    message: str
    """Human-readable status message"""

    object_id: str = FieldInfo(alias="objectId")
    """ID of the vault object being processed"""

    status: Literal["processing", "stored"]
    """Current ingestion status.

    'stored' for file types without text extraction (no chunks/vectors created).
    """

    workflow_id: Optional[str] = FieldInfo(alias="workflowId", default=None)
    """Workflow run ID for tracking progress.

    Null for file types that skip processing.
    """

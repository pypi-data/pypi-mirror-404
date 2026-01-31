# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["V1RetrieveResearchResponse", "Results", "ResultsSection", "ResultsSectionSource", "ResultsSource"]


class ResultsSectionSource(BaseModel):
    snippet: Optional[str] = None

    title: Optional[str] = None

    url: Optional[str] = None


class ResultsSection(BaseModel):
    content: Optional[str] = None

    sources: Optional[List[ResultsSectionSource]] = None

    title: Optional[str] = None


class ResultsSource(BaseModel):
    snippet: Optional[str] = None

    title: Optional[str] = None

    url: Optional[str] = None


class Results(BaseModel):
    """Research findings and analysis"""

    sections: Optional[List[ResultsSection]] = None
    """Detailed research sections"""

    sources: Optional[List[ResultsSource]] = None
    """All sources referenced in research"""

    summary: Optional[str] = None
    """Executive summary of research findings"""


class V1RetrieveResearchResponse(BaseModel):
    id: Optional[str] = None
    """Research task ID"""

    completed_at: Optional[datetime] = FieldInfo(alias="completedAt", default=None)
    """Task completion timestamp"""

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)
    """Task creation timestamp"""

    model: Optional[Literal["fast", "normal", "pro"]] = None
    """Research model used"""

    progress: Optional[float] = None
    """Completion percentage (0-100)"""

    query: Optional[str] = None
    """Original research query"""

    results: Optional[Results] = None
    """Research findings and analysis"""

    status: Optional[Literal["pending", "running", "completed", "failed"]] = None
    """Current status of the research task"""

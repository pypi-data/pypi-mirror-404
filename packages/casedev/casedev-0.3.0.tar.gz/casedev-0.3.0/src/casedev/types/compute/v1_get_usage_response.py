# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["V1GetUsageResponse", "ByEnvironment", "Period", "Summary"]


class ByEnvironment(BaseModel):
    environment: Optional[str] = None

    total_cost_cents: Optional[int] = FieldInfo(alias="totalCostCents", default=None)

    total_cost_formatted: Optional[str] = FieldInfo(alias="totalCostFormatted", default=None)

    total_cpu_seconds: Optional[int] = FieldInfo(alias="totalCpuSeconds", default=None)

    total_gpu_seconds: Optional[int] = FieldInfo(alias="totalGpuSeconds", default=None)

    total_runs: Optional[int] = FieldInfo(alias="totalRuns", default=None)


class Period(BaseModel):
    month: Optional[int] = None

    month_name: Optional[str] = FieldInfo(alias="monthName", default=None)

    year: Optional[int] = None


class Summary(BaseModel):
    total_cost_cents: Optional[int] = FieldInfo(alias="totalCostCents", default=None)

    total_cost_formatted: Optional[str] = FieldInfo(alias="totalCostFormatted", default=None)

    total_cpu_hours: Optional[float] = FieldInfo(alias="totalCpuHours", default=None)

    total_gpu_hours: Optional[float] = FieldInfo(alias="totalGpuHours", default=None)

    total_runs: Optional[int] = FieldInfo(alias="totalRuns", default=None)


class V1GetUsageResponse(BaseModel):
    by_environment: Optional[List[ByEnvironment]] = FieldInfo(alias="byEnvironment", default=None)

    period: Optional[Period] = None

    summary: Optional[Summary] = None

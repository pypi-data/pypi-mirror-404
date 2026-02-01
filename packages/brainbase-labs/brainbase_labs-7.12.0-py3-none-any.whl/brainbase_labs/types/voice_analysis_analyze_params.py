# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Literal, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["VoiceAnalysisAnalyzeParams"]


class VoiceAnalysisAnalyzeParams(TypedDict, total=False):
    deployment_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="deploymentIds")]
    """Optional filter by deployment IDs"""

    end_date: Annotated[Union[str, datetime], PropertyInfo(alias="endDate", format="iso8601")]
    """End date for analysis (ISO 8601)"""

    granularity: Literal["daily", "weekly", "monthly", "yearly"]
    """Time granularity for breakdown"""

    include_call_details: Annotated[bool, PropertyInfo(alias="includeCallDetails")]
    """Include detailed call logs in response"""

    include_transfers: Annotated[bool, PropertyInfo(alias="includeTransfers")]
    """Include transfer analysis"""

    start_date: Annotated[Union[str, datetime], PropertyInfo(alias="startDate", format="iso8601")]
    """Start date for analysis (ISO 8601)"""

    timezone: str
    """Timezone for date calculations"""

    worker_id: Annotated[str, PropertyInfo(alias="workerId")]
    """Optional filter by worker ID"""

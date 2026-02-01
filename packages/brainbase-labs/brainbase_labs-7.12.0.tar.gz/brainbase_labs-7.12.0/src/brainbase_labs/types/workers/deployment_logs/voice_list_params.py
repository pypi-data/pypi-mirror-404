# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Literal, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["VoiceListParams"]


class VoiceListParams(TypedDict, total=False):
    call_sid: Annotated[str, PropertyInfo(alias="callSid")]
    """Filter by Twilio call SID"""

    deployment_id: Annotated[str, PropertyInfo(alias="deploymentId")]
    """Filter logs by deployment id"""

    direction: Literal["inbound", "outbound"]
    """Filter by call direction"""

    end_date: Annotated[Union[str, datetime], PropertyInfo(alias="endDate", format="iso8601")]
    """Deprecated - use start_time_before instead"""

    end_time_after: Annotated[Union[str, datetime], PropertyInfo(alias="endTimeAfter", format="iso8601")]
    """Filter logs with endTime after this date (ISO 8601 format)"""

    end_time_before: Annotated[Union[str, datetime], PropertyInfo(alias="endTimeBefore", format="iso8601")]
    """Filter logs with endTime before this date (ISO 8601 format)"""

    external_call_id: Annotated[str, PropertyInfo(alias="externalCallId")]
    """Filter by external call ID"""

    flow_id: Annotated[str, PropertyInfo(alias="flowId")]
    """Filter logs by flow id"""

    from_number: Annotated[str, PropertyInfo(alias="fromNumber")]
    """Filter by caller phone number (partial match)"""

    limit: int
    """Number of items per page (max 100)"""

    page: int
    """Page number for pagination"""

    search_query: Annotated[str, PropertyInfo(alias="searchQuery")]
    """Search in call transcriptions (case-insensitive)"""

    sort_by: Annotated[
        Literal[
            "startTime",
            "endTime",
            "direction",
            "fromNumber",
            "toNumber",
            "status",
            "externalCallId",
            "createdAt",
            "updatedAt",
        ],
        PropertyInfo(alias="sortBy"),
    ]
    """Field to sort by"""

    sort_order: Annotated[Literal["asc", "desc"], PropertyInfo(alias="sortOrder")]
    """Sort order (ascending or descending)"""

    start_date: Annotated[Union[str, datetime], PropertyInfo(alias="startDate", format="iso8601")]
    """Deprecated - use start_time_after instead"""

    start_time_after: Annotated[Union[str, datetime], PropertyInfo(alias="startTimeAfter", format="iso8601")]
    """Filter logs with startTime after this date (ISO 8601 format)"""

    start_time_before: Annotated[Union[str, datetime], PropertyInfo(alias="startTimeBefore", format="iso8601")]
    """Filter logs with startTime before this date (ISO 8601 format)"""

    status: str
    """Filter by call status"""

    to_number: Annotated[str, PropertyInfo(alias="toNumber")]
    """Filter by called phone number (partial match)"""

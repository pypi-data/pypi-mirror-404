# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["LlmLogListParams"]


class LlmLogListParams(TypedDict, total=False):
    call_id: Annotated[str, PropertyInfo(alias="callId")]
    """Filter by call ID"""

    event_type: Annotated[str, PropertyInfo(alias="eventType")]
    """Filter by event type (beforeRequestHook, afterRequestHook)"""

    limit: int
    """Number of logs to return"""

    offset: int
    """Offset for pagination"""

    session_id: Annotated[str, PropertyInfo(alias="sessionId")]
    """Filter by session ID"""

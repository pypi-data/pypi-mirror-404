# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["LlmLogListResponse", "LlmLog"]


class LlmLog(BaseModel):
    id: str
    """The unique identifier for the log"""

    event_type: str = FieldInfo(alias="eventType")
    """The event type (beforeRequestHook or afterRequestHook)"""

    created_at: str = FieldInfo(alias="createdAt")
    """The timestamp when the log was created"""

    team_id: str = FieldInfo(alias="teamId")
    """The team ID that owns this log"""

    call_id: Optional[str] = FieldInfo(alias="callId", default=None)
    """The call ID associated with this log"""

    session_id: Optional[str] = FieldInfo(alias="sessionId", default=None)
    """The session ID associated with this log"""

    data: Optional[object] = None
    """The log data containing request/response information"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """The timestamp when the log was last updated"""


class LlmLogListResponse(BaseModel):
    logs: List[LlmLog]
    """The list of LLM logs"""

    total: int
    """The total number of logs matching the query"""

    limit: int
    """The limit used for this query"""

    offset: int
    """The offset used for this query"""

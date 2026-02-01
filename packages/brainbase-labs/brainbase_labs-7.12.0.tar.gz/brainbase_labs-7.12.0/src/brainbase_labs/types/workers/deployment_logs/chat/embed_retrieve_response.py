# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ....._models import BaseModel

__all__ = ["EmbedRetrieveResponse"]


class EmbedRetrieveResponse(BaseModel):
    id: str

    expired: bool

    duration: Optional[int] = None

    end_time: Optional[datetime] = FieldInfo(alias="endTime", default=None)

    latency: Optional[object] = None

    message_count: Optional[int] = FieldInfo(alias="messageCount", default=None)

    messages: Optional[object] = None

    origin_url: Optional[str] = FieldInfo(alias="originUrl", default=None)

    session_id: Optional[str] = FieldInfo(alias="sessionId", default=None)

    start_time: Optional[datetime] = FieldInfo(alias="startTime", default=None)

    status: Optional[str] = None

    tool_calls: Optional[object] = FieldInfo(alias="toolCalls", default=None)

    user_agent: Optional[str] = FieldInfo(alias="userAgent", default=None)

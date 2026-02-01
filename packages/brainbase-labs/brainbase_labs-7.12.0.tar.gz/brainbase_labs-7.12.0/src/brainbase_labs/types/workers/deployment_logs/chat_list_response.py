# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import TypeAlias

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["ChatListResponse", "ChatListResponseItem"]


class ChatListResponseItem(BaseModel):
    id: str

    duration: Optional[int] = None

    end_time: Optional[datetime] = FieldInfo(alias="endTime", default=None)

    feedback: Optional[str] = None

    message_count: Optional[int] = FieldInfo(alias="messageCount", default=None)

    messages: Optional[object] = None

    rating: Optional[int] = None

    start_time: Optional[datetime] = FieldInfo(alias="startTime", default=None)

    user_email: Optional[str] = FieldInfo(alias="userEmail", default=None)

    user_id: Optional[str] = FieldInfo(alias="userId", default=None)

    user_name: Optional[str] = FieldInfo(alias="userName", default=None)


ChatListResponse: TypeAlias = List[ChatListResponseItem]

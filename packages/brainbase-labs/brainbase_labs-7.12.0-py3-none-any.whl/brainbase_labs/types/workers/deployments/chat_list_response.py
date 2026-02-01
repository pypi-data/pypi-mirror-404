# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import TypeAlias

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["ChatListResponse", "ChatListResponseItem"]


class ChatListResponseItem(BaseModel):
    id: str

    allowed_users: str = FieldInfo(alias="allowedUsers")

    chat_agent_id: str = FieldInfo(alias="chatAgentId")

    api_model_config: object = FieldInfo(alias="modelConfig")

    llm_model: Optional[str] = FieldInfo(alias="llmModel", default=None)

    welcome_message: Optional[str] = FieldInfo(alias="welcomeMessage", default=None)


ChatListResponse: TypeAlias = List[ChatListResponseItem]

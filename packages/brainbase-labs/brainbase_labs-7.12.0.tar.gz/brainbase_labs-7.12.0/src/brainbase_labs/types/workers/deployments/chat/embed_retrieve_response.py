# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ....._models import BaseModel

__all__ = ["EmbedRetrieveResponse"]


class EmbedRetrieveResponse(BaseModel):
    id: str

    embed_id: str = FieldInfo(alias="embedId")

    agent_logo_url: Optional[str] = FieldInfo(alias="agentLogoUrl", default=None)

    agent_name: Optional[str] = FieldInfo(alias="agentName", default=None)

    primary_color: Optional[str] = FieldInfo(alias="primaryColor", default=None)

    styling: Optional[object] = None

    welcome_message: Optional[str] = FieldInfo(alias="welcomeMessage", default=None)

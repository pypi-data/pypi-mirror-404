# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["TeamRetrieveResponse"]


class TeamRetrieveResponse(BaseModel):
    id: str

    created_at: datetime = FieldInfo(alias="createdAt")

    name: str

    updated_at: datetime = FieldInfo(alias="updatedAt")

    team_owner_id: Optional[str] = FieldInfo(alias="teamOwnerId", default=None)

    twilio_subaccount_auth_token: Optional[str] = FieldInfo(alias="twilioSubaccountAuthToken", default=None)

    twilio_subaccount_sid: Optional[str] = FieldInfo(alias="twilioSubaccountSid", default=None)

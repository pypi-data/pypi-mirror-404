# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from datetime import datetime
from typing_extensions import TypeAlias

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["TeamPhoneHourListResponse", "TeamPhoneHourListResponseItem"]


class TeamPhoneHourListResponseItem(BaseModel):
    id: str

    created_at: datetime = FieldInfo(alias="createdAt")

    hours_id: str = FieldInfo(alias="hoursId")

    phone_number: str = FieldInfo(alias="phoneNumber")

    team_id: str = FieldInfo(alias="teamId")

    updated_at: datetime = FieldInfo(alias="updatedAt")


TeamPhoneHourListResponse: TypeAlias = List[TeamPhoneHourListResponseItem]

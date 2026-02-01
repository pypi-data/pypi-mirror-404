# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import TypeAlias

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["BusinessHourListResponse", "BusinessHourListResponseItem"]


class BusinessHourListResponseItem(BaseModel):
    id: str

    created_at: datetime = FieldInfo(alias="createdAt")

    hours: object

    timezone: str

    updated_at: datetime = FieldInfo(alias="updatedAt")

    primary_tag: Optional[str] = FieldInfo(alias="primaryTag", default=None)

    secondary_tag: Optional[str] = FieldInfo(alias="secondaryTag", default=None)


BusinessHourListResponse: TypeAlias = List[BusinessHourListResponseItem]

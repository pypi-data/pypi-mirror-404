# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["BusinessHourUpdateResponse"]


class BusinessHourUpdateResponse(BaseModel):
    id: str

    created_at: datetime = FieldInfo(alias="createdAt")

    hours: object

    timezone: str

    updated_at: datetime = FieldInfo(alias="updatedAt")

    primary_tag: Optional[str] = FieldInfo(alias="primaryTag", default=None)

    secondary_tag: Optional[str] = FieldInfo(alias="secondaryTag", default=None)

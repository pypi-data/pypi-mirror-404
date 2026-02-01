# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["Integration"]


class Integration(BaseModel):
    id: str

    app_type: str = FieldInfo(alias="appType")

    config: object

    created_at: datetime = FieldInfo(alias="createdAt")

    updated_at: datetime = FieldInfo(alias="updatedAt")

    description: Optional[str] = None

    name: Optional[str] = None

    team_id: Optional[str] = FieldInfo(alias="teamId", default=None)

    worker_id: Optional[str] = FieldInfo(alias="workerId", default=None)

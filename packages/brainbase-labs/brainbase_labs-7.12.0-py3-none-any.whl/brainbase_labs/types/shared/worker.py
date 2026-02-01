# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["Worker"]


class Worker(BaseModel):
    id: str

    created_at: datetime = FieldInfo(alias="createdAt")

    engine_version: str = FieldInfo(alias="engineVersion")

    name: str

    team_id: str = FieldInfo(alias="teamId")

    updated_at: datetime = FieldInfo(alias="updatedAt")

    description: Optional[str] = None

    icon: Optional[str] = None

    last_refreshed_at: Optional[datetime] = FieldInfo(alias="lastRefreshedAt", default=None)

    status: Optional[str] = None

    visualizations: Optional[object] = None

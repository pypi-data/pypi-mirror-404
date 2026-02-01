# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["Flow"]


class Flow(BaseModel):
    id: str

    code: str

    created_at: datetime = FieldInfo(alias="createdAt")

    name: str

    updated_at: datetime = FieldInfo(alias="updatedAt")

    variables: object

    version: int

    worker_id: str = FieldInfo(alias="workerId")

    label: Optional[str] = None

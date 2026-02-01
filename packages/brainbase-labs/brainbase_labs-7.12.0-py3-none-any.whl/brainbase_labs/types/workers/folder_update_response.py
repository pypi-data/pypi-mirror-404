# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["FolderUpdateResponse"]


class FolderUpdateResponse(BaseModel):
    id: str

    created_at: datetime = FieldInfo(alias="createdAt")

    name: str

    updated_at: datetime = FieldInfo(alias="updatedAt")

    worker_id: str = FieldInfo(alias="workerId")

    description: Optional[str] = None

    graph_metadata: Optional[object] = FieldInfo(alias="graphMetadata", default=None)

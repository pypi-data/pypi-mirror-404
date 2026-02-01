# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["TestCreateResponse"]


class TestCreateResponse(BaseModel):
    __test__ = False
    id: str

    checkpoints: object

    created_at: datetime = FieldInfo(alias="createdAt")

    flow_id: str = FieldInfo(alias="flowId")

    name: str

    system_prompt: str = FieldInfo(alias="systemPrompt")

    test_mode: str = FieldInfo(alias="testMode")

    updated_at: datetime = FieldInfo(alias="updatedAt")

    worker_id: str = FieldInfo(alias="workerId")

    description: Optional[str] = None

    websocket_url: Optional[str] = FieldInfo(alias="websocketUrl", default=None)

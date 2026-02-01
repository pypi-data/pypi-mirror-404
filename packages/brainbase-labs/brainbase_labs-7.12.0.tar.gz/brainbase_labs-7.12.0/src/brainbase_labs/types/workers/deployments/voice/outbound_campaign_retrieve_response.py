# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ....._models import BaseModel

__all__ = ["OutboundCampaignRetrieveResponse"]


class OutboundCampaignRetrieveResponse(BaseModel):
    id: str

    batch_interval_minutes: int = FieldInfo(alias="batchIntervalMinutes")

    batch_size: int = FieldInfo(alias="batchSize")

    created_at: datetime = FieldInfo(alias="createdAt")

    data: object

    deployment_id: str = FieldInfo(alias="deploymentId")

    status: str

    team_id: str = FieldInfo(alias="teamId")

    updated_at: datetime = FieldInfo(alias="updatedAt")

    worker_id: str = FieldInfo(alias="workerId")

    additional_data: Optional[object] = FieldInfo(alias="additionalData", default=None)

    created_by_id: Optional[str] = FieldInfo(alias="createdById", default=None)

    description: Optional[str] = None

    flow_id: Optional[str] = FieldInfo(alias="flowId", default=None)

    name: Optional[str] = None

    telephony_provider: Optional[object] = FieldInfo(alias="telephonyProvider", default=None)

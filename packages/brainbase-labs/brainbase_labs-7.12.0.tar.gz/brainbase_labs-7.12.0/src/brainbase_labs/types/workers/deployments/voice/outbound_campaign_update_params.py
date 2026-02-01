# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal, Required, Annotated, TypedDict

from ....._utils import PropertyInfo

__all__ = ["OutboundCampaignUpdateParams"]


class OutboundCampaignUpdateParams(TypedDict, total=False):
    worker_id: Required[Annotated[str, PropertyInfo(alias="workerId")]]

    deployment_id: Required[Annotated[str, PropertyInfo(alias="deploymentId")]]

    additional_data: object

    batch_interval_minutes: int

    batch_size: int

    data: Iterable[object]

    description: str

    name: str

    status: Literal["CREATED", "STARTED", "RUNNING", "COMPLETED", "STOPPED", "FAILED"]

    telephony_provider: Annotated[object, PropertyInfo(alias="telephonyProvider")]

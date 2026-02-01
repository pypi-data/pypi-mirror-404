# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from ......_utils import PropertyInfo

__all__ = ["DataUpdateParams"]


class DataUpdateParams(TypedDict, total=False):
    worker_id: Required[Annotated[str, PropertyInfo(alias="workerId")]]

    deployment_id: Required[Annotated[str, PropertyInfo(alias="deploymentId")]]

    campaign_id: Required[Annotated[str, PropertyInfo(alias="campaignId")]]

    result: object

    row_data: Annotated[object, PropertyInfo(alias="rowData")]

    status: Literal["PENDING", "PROCESSING", "COMPLETED", "FAILED"]

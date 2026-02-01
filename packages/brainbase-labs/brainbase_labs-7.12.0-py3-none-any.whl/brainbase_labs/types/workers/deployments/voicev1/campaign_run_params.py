# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal, Required, Annotated, TypedDict

from ....._utils import PropertyInfo

__all__ = ["CampaignRunParams", "Data"]


class CampaignRunParams(TypedDict, total=False):
    worker_id: Required[Annotated[str, PropertyInfo(alias="workerId")]]

    deployment_id: Required[Annotated[str, PropertyInfo(alias="deploymentId")]]

    data: Required[Iterable[Data]]
    """Array of data objects to process in the campaign"""


class Data(TypedDict, total=False):
    id: Required[str]
    """Unique identifier for the data row"""

    phone_number: Required[Annotated[str, PropertyInfo(alias="phoneNumber")]]
    """Phone number to call in E.164 format (e.g., +12345678901)"""

    status: Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"]
    """Status of the call"""

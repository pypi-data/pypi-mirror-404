# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal, Required, Annotated, TypedDict

from ....._utils import PropertyInfo

__all__ = ["OutboundCampaignCreateParams"]


class OutboundCampaignCreateParams(TypedDict, total=False):
    worker_id: Required[Annotated[str, PropertyInfo(alias="workerId")]]

    data: Required[Iterable[object]]
    """Contact data array"""

    additional_data: object
    """Additional metadata"""

    batch_interval_minutes: int
    """Minutes to wait between batches"""

    batch_size: int
    """Number of calls to make simultaneously"""

    created_by: str
    """User ID who created the campaign"""

    description: str
    """Campaign description"""

    flow_id: str
    """Flow ID"""

    name: str
    """Campaign name"""

    status: Literal["CREATED", "STARTED", "RUNNING", "COMPLETED", "STOPPED", "FAILED"]
    """Campaign status"""

    team_id: str
    """Team ID"""

    telephony_provider: Annotated[object, PropertyInfo(alias="telephonyProvider")]
    """Telephony provider configuration"""

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["BusinessHourUpdateParams"]


class BusinessHourUpdateParams(TypedDict, total=False):
    hours: Dict[str, str]
    """JSON object containing business hours configuration"""

    primary_tag: Annotated[str, PropertyInfo(alias="primaryTag")]
    """Primary tag for categorization (e.g., business name, location)"""

    secondary_tag: Annotated[str, PropertyInfo(alias="secondaryTag")]
    """Secondary tag for categorization (e.g., department, type)"""

    timezone: str
    """
    Timezone for the business hours (e.g., 'America/New_York', 'UTC',
    'Europe/London')
    """

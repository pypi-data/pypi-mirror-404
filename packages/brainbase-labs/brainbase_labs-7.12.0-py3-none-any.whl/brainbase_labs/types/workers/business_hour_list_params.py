# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["BusinessHourListParams"]


class BusinessHourListParams(TypedDict, total=False):
    include_team_phone_hours: Annotated[bool, PropertyInfo(alias="includeTeamPhoneHours")]
    """Set to true to include related team phone hours"""

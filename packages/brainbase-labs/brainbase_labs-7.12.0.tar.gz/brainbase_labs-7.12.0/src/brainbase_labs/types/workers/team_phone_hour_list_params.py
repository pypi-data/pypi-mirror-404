# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["TeamPhoneHourListParams"]


class TeamPhoneHourListParams(TypedDict, total=False):
    include_relations: Annotated[bool, PropertyInfo(alias="includeRelations")]
    """Set to true to include related business hours and team"""

    phone_number: Annotated[str, PropertyInfo(alias="phoneNumber")]
    """Filter by phone number"""

    team_id: Annotated[str, PropertyInfo(alias="teamId")]
    """Filter by team ID"""

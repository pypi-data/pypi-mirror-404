# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["TeamPhoneHourRetrieveParams"]


class TeamPhoneHourRetrieveParams(TypedDict, total=False):
    include_relations: Annotated[bool, PropertyInfo(alias="includeRelations")]
    """Set to true to include related business hours and team"""

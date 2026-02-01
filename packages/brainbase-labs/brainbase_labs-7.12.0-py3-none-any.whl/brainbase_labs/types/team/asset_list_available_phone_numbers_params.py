# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["AssetListAvailablePhoneNumbersParams"]


class AssetListAvailablePhoneNumbersParams(TypedDict, total=False):
    country_code: Required[Annotated[str, PropertyInfo(alias="countryCode")]]
    """Two-letter ISO country code (e.g. US, GB)."""

    number_type: Required[Annotated[Literal["Local", "Mobile", "TollFree"], PropertyInfo(alias="numberType")]]
    """Type of phone number."""

    area_code: Annotated[str, PropertyInfo(alias="areaCode")]
    """Filter by area code."""

    contains: str
    """Filter by pattern contained in number."""

    mms_enabled: Annotated[bool, PropertyInfo(alias="mmsEnabled")]
    """Filter for MMS-enabled numbers."""

    sms_enabled: Annotated[bool, PropertyInfo(alias="smsEnabled")]
    """Filter for SMS-enabled numbers."""

    voice_enabled: Annotated[bool, PropertyInfo(alias="voiceEnabled")]
    """Filter for voice-enabled numbers."""

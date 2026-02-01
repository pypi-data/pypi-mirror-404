# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["AssetPurchasePhoneNumbersParams"]


class AssetPurchasePhoneNumbersParams(TypedDict, total=False):
    phone_numbers: Required[Annotated[SequenceNotStr[str], PropertyInfo(alias="phoneNumbers")]]
    """Array of phone numbers to purchase in E.164 format."""

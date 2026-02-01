# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["AssetPurchaseWhatsappSenderParams", "Profile"]


class AssetPurchaseWhatsappSenderParams(TypedDict, total=False):
    phone_number: Required[Annotated[str, PropertyInfo(alias="phoneNumber")]]
    """Phone number in E.164 format."""

    profile: Required[Profile]


class Profile(TypedDict, total=False):
    name: Required[str]
    """WhatsApp display name."""

    about: str

    address: str

    description: str

    emails: SequenceNotStr[str]

    logo_url: Annotated[str, PropertyInfo(alias="logoUrl")]

    vertical: str

    websites: SequenceNotStr[str]

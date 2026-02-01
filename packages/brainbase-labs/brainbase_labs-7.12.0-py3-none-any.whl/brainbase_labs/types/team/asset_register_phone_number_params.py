# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["AssetRegisterPhoneNumberParams"]


class AssetRegisterPhoneNumberParams(TypedDict, total=False):
    integration_id: Required[Annotated[str, PropertyInfo(alias="integrationId")]]

    phone_number: Required[Annotated[str, PropertyInfo(alias="phoneNumber")]]

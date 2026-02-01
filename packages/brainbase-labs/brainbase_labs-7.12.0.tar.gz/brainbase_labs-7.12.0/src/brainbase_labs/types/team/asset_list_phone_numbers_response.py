# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import TypeAlias

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["AssetListPhoneNumbersResponse", "AssetListPhoneNumbersResponseItem"]


class AssetListPhoneNumbersResponseItem(BaseModel):
    id: str

    a2p_verified: bool = FieldInfo(alias="a2pVerified")

    created_at: datetime = FieldInfo(alias="createdAt")

    phone_number: str = FieldInfo(alias="phoneNumber")

    provider: str

    updated_at: datetime = FieldInfo(alias="updatedAt")

    caller_name: Optional[str] = FieldInfo(alias="callerName", default=None)

    country_code: Optional[str] = FieldInfo(alias="countryCode", default=None)

    integration_id: Optional[str] = FieldInfo(alias="integrationId", default=None)

    metadata: Optional[object] = None

    team_id: Optional[str] = FieldInfo(alias="teamId", default=None)

    worker_id: Optional[str] = FieldInfo(alias="workerId", default=None)


AssetListPhoneNumbersResponse: TypeAlias = List[AssetListPhoneNumbersResponseItem]

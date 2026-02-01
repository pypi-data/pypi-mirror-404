# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["TeamRetrieveSubaccountCredentialsResponse"]


class TeamRetrieveSubaccountCredentialsResponse(BaseModel):
    account_sid: Optional[str] = FieldInfo(alias="accountSid", default=None)

    auth_token: Optional[str] = FieldInfo(alias="authToken", default=None)

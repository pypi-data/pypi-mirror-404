# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["TwilioCreateParams"]


class TwilioCreateParams(TypedDict, total=False):
    account_sid: Required[Annotated[str, PropertyInfo(alias="accountSid")]]

    auth_token: Required[Annotated[str, PropertyInfo(alias="authToken")]]
    """Provide the plain text auth token. It will be encrypted before being stored."""

    description: str

    name: str

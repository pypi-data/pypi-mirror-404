# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["WorkerCheckCallableParams"]


class WorkerCheckCallableParams(TypedDict, total=False):
    phone_number: Required[Annotated[str, PropertyInfo(alias="phoneNumber")]]
    """The phone number to check (accepts any format - will be normalized)"""

    timestamp: Required[float]
    """Unix timestamp in seconds (UTC).

    Will be converted to the business hours timezone.
    """

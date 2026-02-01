# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["TeamPhoneHourCreateParams"]


class TeamPhoneHourCreateParams(TypedDict, total=False):
    hours_id: Required[Annotated[str, PropertyInfo(alias="hoursId")]]

    phone_number: Required[Annotated[str, PropertyInfo(alias="phoneNumber")]]

    team_id: Required[Annotated[str, PropertyInfo(alias="teamId")]]

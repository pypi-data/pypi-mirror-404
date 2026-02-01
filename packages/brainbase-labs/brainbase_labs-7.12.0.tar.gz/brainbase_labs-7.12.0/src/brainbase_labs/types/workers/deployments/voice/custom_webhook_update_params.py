# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from ....._utils import PropertyInfo

__all__ = ["CustomWebhookUpdateParams"]


class CustomWebhookUpdateParams(TypedDict, total=False):
    worker_id: Required[Annotated[str, PropertyInfo(alias="workerId")]]

    deployment_id: Required[Annotated[str, PropertyInfo(alias="deploymentId")]]

    active: bool

    fields: str

    method: Literal["GET", "POST", "PUT", "PATCH"]

    name: str

    url: str

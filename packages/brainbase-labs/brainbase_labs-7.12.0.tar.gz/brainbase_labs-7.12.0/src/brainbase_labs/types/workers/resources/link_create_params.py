# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["LinkCreateParams"]


class LinkCreateParams(TypedDict, total=False):
    name: Required[str]

    raw_link: Required[Annotated[str, PropertyInfo(alias="rawLink")]]

    update_frequency: Required[Annotated[str, PropertyInfo(alias="updateFrequency")]]

    folder_id: Annotated[str, PropertyInfo(alias="folderId")]

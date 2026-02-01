# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["TeamRetrieveParams"]


class TeamRetrieveParams(TypedDict, total=False):
    include_integrations: Annotated[bool, PropertyInfo(alias="includeIntegrations")]
    """Set to true to also include integrations in the response."""

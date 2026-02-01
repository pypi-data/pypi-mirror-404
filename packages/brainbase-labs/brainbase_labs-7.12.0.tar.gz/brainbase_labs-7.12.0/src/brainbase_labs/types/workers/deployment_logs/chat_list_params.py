# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["ChatListParams"]


class ChatListParams(TypedDict, total=False):
    deployment_id: Annotated[str, PropertyInfo(alias="deploymentId")]
    """Filter logs by deployment id"""

    flow_id: Annotated[str, PropertyInfo(alias="flowId")]
    """Filter logs by flow id"""

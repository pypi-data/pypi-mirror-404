# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

__all__ = ["FlowCreateParams"]


class FlowCreateParams(TypedDict, total=False):
    code: Required[str]

    label: Required[Optional[str]]

    name: Required[str]

    validate: bool

    variables: str

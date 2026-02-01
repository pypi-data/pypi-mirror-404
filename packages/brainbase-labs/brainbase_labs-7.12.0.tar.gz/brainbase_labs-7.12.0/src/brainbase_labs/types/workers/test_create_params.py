# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["TestCreateParams", "Checkpoint"]


class TestCreateParams(TypedDict, total=False):
    checkpoints: Required[Iterable[Checkpoint]]

    description: Required[str]

    flow_id: Required[Annotated[str, PropertyInfo(alias="flowId")]]

    name: Required[str]

    system_prompt: Required[Annotated[str, PropertyInfo(alias="systemPrompt")]]

    test_mode: Required[Annotated[str, PropertyInfo(alias="testMode")]]


class Checkpoint(TypedDict, total=False):
    description: Required[str]

    name: Required[str]

    runs: Required[float]

    tolerance: Required[float]

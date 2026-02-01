# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["TestUpdateParams", "Checkpoint"]


class TestUpdateParams(TypedDict, total=False):
    worker_id: Required[Annotated[str, PropertyInfo(alias="workerId")]]

    checkpoints: Iterable[Checkpoint]

    description: str

    flow_id: Annotated[str, PropertyInfo(alias="flowId")]

    name: str

    system_prompt: Annotated[str, PropertyInfo(alias="systemPrompt")]

    test_mode: Annotated[str, PropertyInfo(alias="testMode")]


class Checkpoint(TypedDict, total=False):
    description: Required[str]

    name: Required[str]

    runs: Required[float]

    tolerance: Required[float]

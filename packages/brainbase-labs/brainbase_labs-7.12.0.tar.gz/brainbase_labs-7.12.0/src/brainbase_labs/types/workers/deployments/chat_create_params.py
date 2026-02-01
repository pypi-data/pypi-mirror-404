# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable
from typing_extensions import Literal, Required, Annotated, TypedDict

from ...._types import SequenceNotStr
from ...._utils import PropertyInfo

__all__ = ["ChatCreateParams", "Extractions", "SuccessCriterion", "SuccessCriterionItem"]


class ChatCreateParams(TypedDict, total=False):
    flow_id: Required[Annotated[str, PropertyInfo(alias="flowId")]]

    name: Required[str]

    allowed_users: Annotated[SequenceNotStr[str], PropertyInfo(alias="allowedUsers")]

    extractions: Dict[str, Extractions]

    llm_model: Annotated[str, PropertyInfo(alias="llmModel")]

    model_config: Annotated[Dict[str, str], PropertyInfo(alias="modelConfig")]

    success_criteria: Annotated[Iterable[SuccessCriterion], PropertyInfo(alias="successCriteria")]

    welcome_message: Annotated[str, PropertyInfo(alias="welcomeMessage")]


class Extractions(TypedDict, total=False):
    description: Required[str]

    type: Required[Literal["string", "number", "boolean"]]

    required: bool


class SuccessCriterionItem(TypedDict, total=False):
    description: Required[str]

    threshold: Required[float]

    title: Required[str]

    type: Required[Literal["BINARY", "SCORE"]]


class SuccessCriterion(TypedDict, total=False):
    items: Required[Iterable[SuccessCriterionItem]]

    title: Required[str]

    description: str

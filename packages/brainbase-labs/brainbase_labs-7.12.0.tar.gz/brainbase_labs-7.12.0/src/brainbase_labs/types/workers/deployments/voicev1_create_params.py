# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Literal, Required, Annotated, TypedDict

from ...._types import SequenceNotStr
from ...._utils import PropertyInfo

__all__ = ["Voicev1CreateParams", "Extractions"]


class Voicev1CreateParams(TypedDict, total=False):
    allowed_transfer_numbers: Required[Annotated[SequenceNotStr[str], PropertyInfo(alias="allowedTransferNumbers")]]

    config: Required[object]

    end_sentence: Required[Annotated[Optional[str], PropertyInfo(alias="endSentence")]]

    flow_id: Required[Annotated[str, PropertyInfo(alias="flowId")]]

    functions: Required[Optional[str]]

    language: Required[Optional[str]]

    model: Required[Optional[str]]

    name: Required[str]

    objective: Required[str]

    phone_number: Required[Annotated[str, PropertyInfo(alias="phoneNumber")]]

    resource_keys: Required[Annotated[SequenceNotStr[str], PropertyInfo(alias="resourceKeys")]]

    start_sentence: Required[Annotated[Optional[str], PropertyInfo(alias="startSentence")]]

    voice_id: Required[Annotated[Optional[str], PropertyInfo(alias="voiceId")]]

    ws_base_url: Required[Annotated[Optional[str], PropertyInfo(alias="wsBaseUrl")]]

    extractions: Dict[str, Extractions]


class Extractions(TypedDict, total=False):
    description: Required[str]

    type: Required[Literal["string", "number", "boolean"]]

    required: bool

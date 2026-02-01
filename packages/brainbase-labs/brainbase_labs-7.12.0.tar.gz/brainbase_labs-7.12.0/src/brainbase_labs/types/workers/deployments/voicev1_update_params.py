# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Literal, Required, Annotated, TypedDict

from ...._types import SequenceNotStr
from ...._utils import PropertyInfo

__all__ = ["Voicev1UpdateParams", "Extractions"]


class Voicev1UpdateParams(TypedDict, total=False):
    worker_id: Required[Annotated[str, PropertyInfo(alias="workerId")]]

    allowed_transfer_numbers: Annotated[SequenceNotStr[str], PropertyInfo(alias="allowedTransferNumbers")]

    config: str

    end_sentence: Annotated[Optional[str], PropertyInfo(alias="endSentence")]

    extractions: Dict[str, Extractions]

    flow_id: Annotated[str, PropertyInfo(alias="flowId")]

    functions: Optional[str]

    language: Optional[str]

    model: Optional[str]

    name: str

    objective: str

    phone_number: Annotated[str, PropertyInfo(alias="phoneNumber")]

    resource_keys: Annotated[SequenceNotStr[str], PropertyInfo(alias="resourceKeys")]

    start_sentence: Annotated[Optional[str], PropertyInfo(alias="startSentence")]

    voice_id: Annotated[Optional[str], PropertyInfo(alias="voiceId")]

    ws_base_url: Annotated[Optional[str], PropertyInfo(alias="wsBaseUrl")]


class Extractions(TypedDict, total=False):
    description: Required[str]

    type: Required[Literal["string", "number", "boolean"]]

    required: bool

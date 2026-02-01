# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable, Optional
from typing_extensions import Required, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["VoiceMakeBatchCallsParams"]


class VoiceMakeBatchCallsParams(TypedDict, total=False):
    worker_id: Required[Annotated[str, PropertyInfo(alias="workerId")]]

    data: Required[Iterable[Dict[str, str]]]

    additional_data: str

    batch_interval_minutes: float

    batch_size: float

    condition: Optional[str]

    country: str

    extractions: Optional[str]

    ws_url: Annotated[str, PropertyInfo(alias="wsUrl")]

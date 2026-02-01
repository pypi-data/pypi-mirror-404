# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ...._types import SequenceNotStr
from ...._utils import PropertyInfo

__all__ = ["DefaultCheckUpdateParams"]


class DefaultCheckUpdateParams(TypedDict, total=False):
    worker_id: Required[Annotated[str, PropertyInfo(alias="workerId")]]

    ai_enabled: Annotated[bool, PropertyInfo(alias="aiEnabled")]

    ai_threshold: Annotated[float, PropertyInfo(alias="aiThreshold")]

    alert_emails: Annotated[SequenceNotStr[str], PropertyInfo(alias="alertEmails")]

    api_enabled: Annotated[bool, PropertyInfo(alias="apiEnabled")]

    api_threshold: Annotated[float, PropertyInfo(alias="apiThreshold")]

    enabled: bool

    latency_enabled: Annotated[bool, PropertyInfo(alias="latencyEnabled")]

    latency_threshold: Annotated[float, PropertyInfo(alias="latencyThreshold")]

    sample_rate: Annotated[float, PropertyInfo(alias="sampleRate")]

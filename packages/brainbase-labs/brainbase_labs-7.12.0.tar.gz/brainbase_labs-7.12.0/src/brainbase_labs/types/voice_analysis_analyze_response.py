# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["VoiceAnalysisAnalyzeResponse", "Summary"]


class Summary(BaseModel):
    average_call_duration: Optional[float] = FieldInfo(alias="averageCallDuration", default=None)

    total_calls: Optional[float] = FieldInfo(alias="totalCalls", default=None)

    total_minutes: Optional[float] = FieldInfo(alias="totalMinutes", default=None)

    total_transfer_minutes: Optional[float] = FieldInfo(alias="totalTransferMinutes", default=None)

    total_transfers: Optional[float] = FieldInfo(alias="totalTransfers", default=None)


class VoiceAnalysisAnalyzeResponse(BaseModel):
    summary: Optional[Summary] = None

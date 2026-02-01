# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["VoiceStopBatchCallsResponse"]


class VoiceStopBatchCallsResponse(BaseModel):
    message: Optional[str] = None

    removed_count: Optional[int] = FieldInfo(alias="removedCount", default=None)

    removed_items: Optional[List[object]] = FieldInfo(alias="removedItems", default=None)

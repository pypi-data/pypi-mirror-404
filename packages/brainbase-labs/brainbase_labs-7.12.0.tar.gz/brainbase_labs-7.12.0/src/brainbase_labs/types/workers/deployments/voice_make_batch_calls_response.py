# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["VoiceMakeBatchCallsResponse"]


class VoiceMakeBatchCallsResponse(BaseModel):
    message: Optional[str] = None

    rows_processed: Optional[int] = FieldInfo(alias="rowsProcessed", default=None)

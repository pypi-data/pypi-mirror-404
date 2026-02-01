# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel

__all__ = ["WorkerRetrieveSessionResponse"]


class WorkerRetrieveSessionResponse(BaseModel):
    id: Optional[str] = None

    error: Optional[object] = None

    flow_id: Optional[str] = None

    input_tokens: Optional[int] = None

    messages: Optional[List[object]] = None

    minutes: Optional[float] = None

    output_tokens: Optional[int] = None

    session_end: Optional[str] = None

    session_start: Optional[str] = None

    state: Optional[object] = None

    status: Optional[str] = None

    trace: Optional[List[object]] = None

    worker_id: Optional[str] = None

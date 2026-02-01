# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["ResourceQueryResponse"]


class ResourceQueryResponse(BaseModel):
    data: Optional[object] = None
    """Query result data from the RAG service"""

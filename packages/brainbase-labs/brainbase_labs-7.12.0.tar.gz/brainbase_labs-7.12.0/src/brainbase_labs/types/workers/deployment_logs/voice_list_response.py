# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel
from ...shared.log import Log

__all__ = ["VoiceListResponse", "Pagination"]


class Pagination(BaseModel):
    has_next: Optional[bool] = FieldInfo(alias="hasNext", default=None)
    """Whether there is a next page"""

    has_prev: Optional[bool] = FieldInfo(alias="hasPrev", default=None)
    """Whether there is a previous page"""

    limit: Optional[int] = None
    """Items per page"""

    page: Optional[int] = None
    """Current page number"""

    total: Optional[int] = None
    """Total number of items"""

    total_pages: Optional[int] = FieldInfo(alias="totalPages", default=None)
    """Total number of pages"""


class VoiceListResponse(BaseModel):
    data: Optional[List[Log]] = None

    pagination: Optional[Pagination] = None

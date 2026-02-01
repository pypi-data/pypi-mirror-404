# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["WorkerCheckCallableResponse"]


class WorkerCheckCallableResponse(BaseModel):
    callable: Optional[bool] = None
    """Whether the phone number is callable at the given time"""

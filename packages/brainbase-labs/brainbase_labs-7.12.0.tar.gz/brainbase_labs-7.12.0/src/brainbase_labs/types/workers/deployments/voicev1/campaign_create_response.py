# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from ....._models import BaseModel

__all__ = ["CampaignCreateResponse"]


class CampaignCreateResponse(BaseModel):
    id: Optional[str] = None

    status: Optional[Literal["RUNNING", "COMPLETED", "FAILED"]] = None

    steps: Optional[List[object]] = None

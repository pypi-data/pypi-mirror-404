# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable
from typing_extensions import Literal, Required, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["Voicev1MakeBatchCallsParams", "Data", "Extractions"]


class Voicev1MakeBatchCallsParams(TypedDict, total=False):
    worker_id: Required[Annotated[str, PropertyInfo(alias="workerId")]]

    data: Required[Iterable[Data]]
    """
    Array of data objects to process in batches, each requiring at least an id and
    phoneNumber
    """

    additional_data: Dict[str, str]
    """
    Additional data to pass with each request that will be available during the call
    """

    batch_interval_minutes: float
    """Time interval between batches in minutes (default 5)"""

    batch_size: float
    """Number of items to process in each batch (default 10)"""

    condition: str
    """Optional condition to evaluate for processing data.

    Supports template variables like {{variableName}}
    """

    extractions: Dict[str, Extractions]
    """
    Definitions of data to extract during calls, with each key representing a field
    to extract
    """

    ws_url: Annotated[str, PropertyInfo(alias="wsUrl")]
    """Webhook URL to receive events when calls complete or extract data"""


class Data(TypedDict, total=False):
    id: Required[str]
    """Unique identifier for the data row"""

    phone_number: Required[Annotated[str, PropertyInfo(alias="phoneNumber")]]
    """Phone number to call in E.164 format (e.g., +12345678901)"""

    status: Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"]
    """Status of the call"""


class Extractions(TypedDict, total=False):
    description: Required[str]
    """Description of what this extraction represents"""

    type: Required[Literal["string", "number", "boolean", "object", "array"]]
    """The data type of the extraction"""

    example: str
    """Example value for this extraction"""

    required: bool
    """Whether this extraction is required"""

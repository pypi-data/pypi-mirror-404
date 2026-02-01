# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["Log"]


class Log(BaseModel):
    """Voice deployment log data with call details and transcription"""
    
    id: str

    call_sid: Optional[str] = None

    data: Optional[object] = None

    direction: Optional[str] = None

    duration: Optional[int] = None

    end_time: Optional[datetime] = FieldInfo(alias="endTime", default=None)

    external_call_id: Optional[str] = FieldInfo(alias="externalCallId", default=None)

    from_number: Optional[str] = FieldInfo(alias="fromNumber", default=None)

    messages: Optional[object] = None

    recording_url: Optional[str] = FieldInfo(alias="recordingUrl", default=None)

    start_time: Optional[datetime] = FieldInfo(alias="startTime", default=None)

    status: Optional[str] = None

    telephony_source: Optional[str] = FieldInfo(alias="Telephony_source", default=None)

    to_number: Optional[str] = FieldInfo(alias="toNumber", default=None)

    transcription: Optional[str] = None

    # Additional metadata fields
    twilio_body: Optional[object] = FieldInfo(alias="twilioBody", default=None)
    """Twilio webhook payload data"""

    outbound_data: Optional[object] = FieldInfo(alias="outbound_data", default=None)
    """Outbound campaign data if applicable"""

    session_data: Optional[object] = FieldInfo(alias="sessionData", default=None)
    """Session state and trace data"""

    error: Optional[object] = None
    """Error information if call failed"""

    input_tokens: Optional[int] = FieldInfo(alias="input_tokens", default=None)
    """LLM input tokens used"""

    output_tokens: Optional[int] = FieldInfo(alias="output_tokens", default=None)
    """LLM output tokens used"""

    transfer_data: Optional[object] = FieldInfo(alias="transferData", default=None)
    """Twilio transfer data including duration and status"""

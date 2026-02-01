# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["VoiceV1Deployment"]


class VoiceV1Deployment(BaseModel):
    id: str

    allowed_transfer_numbers: str = FieldInfo(alias="allowedTransferNumbers")

    objective: str

    phone_number: str = FieldInfo(alias="phoneNumber")

    resource_keys: str = FieldInfo(alias="resourceKeys")

    end_sentence: Optional[str] = FieldInfo(alias="endSentence", default=None)

    functions: Optional[object] = None

    language: Optional[str] = None

    model: Optional[str] = None

    start_sentence: Optional[str] = FieldInfo(alias="startSentence", default=None)

    voice_id: Optional[str] = FieldInfo(alias="voiceId", default=None)

    ws_base_url: Optional[str] = FieldInfo(alias="wsBaseUrl", default=None)

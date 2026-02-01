# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["CustomVoiceCreateParams"]


class CustomVoiceCreateParams(TypedDict, total=False):
    elevenlabs_voice_id: Required[Annotated[str, PropertyInfo(alias="elevenlabsVoiceId")]]
    """The ElevenLabs voice ID (name and owner are fetched automatically)"""

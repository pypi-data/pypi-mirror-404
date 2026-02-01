# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from ...shared.voice_deployment import VoiceDeployment

__all__ = ["VoiceListResponse"]

VoiceListResponse: TypeAlias = List[VoiceDeployment]

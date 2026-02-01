# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Required, Annotated, TypedDict

from ....._utils import PropertyInfo

__all__ = ["EmbedUpdateParams"]


class EmbedUpdateParams(TypedDict, total=False):
    worker_id: Required[Annotated[str, PropertyInfo(alias="workerId")]]

    agent_logo_url: Annotated[str, PropertyInfo(alias="agentLogoUrl")]

    agent_name: Annotated[str, PropertyInfo(alias="agentName")]

    flow_id: Annotated[str, PropertyInfo(alias="flowId")]

    name: str

    primary_color: Annotated[str, PropertyInfo(alias="primaryColor")]

    styling: Dict[str, str]

    welcome_message: Annotated[str, PropertyInfo(alias="welcomeMessage")]

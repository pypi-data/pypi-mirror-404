# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["RuntimeErrorRecordParams"]


class RuntimeErrorRecordParams(TypedDict, total=False):
    error: Required[str]
    """Error message"""

    service: Required[str]
    """Service that generated the error (e.g., "based_engine", "sms")"""

    type: Required[str]
    """Error type/class (e.g., "ValueError", "RuntimeError")"""

    bb_engine_session_id: Annotated[str, PropertyInfo(alias="bbEngineSessionId")]
    """Session ID for trace correlation"""

    deployment_id: Annotated[str, PropertyInfo(alias="deploymentId")]
    """Deployment ID (optional)"""

    flow_id: Annotated[str, PropertyInfo(alias="flowId")]
    """Flow ID (used to lookup deployment if deploymentId not provided)"""

    function_name: Annotated[str, PropertyInfo(alias="functionName")]
    """Function being executed when error occurred"""

    line_number: Annotated[int, PropertyInfo(alias="lineNumber")]
    """Line number in Based code"""

    metadata: object
    """Additional context"""

    severity: Literal["warning", "error", "critical"]

    traceback: str
    """Full stack trace"""

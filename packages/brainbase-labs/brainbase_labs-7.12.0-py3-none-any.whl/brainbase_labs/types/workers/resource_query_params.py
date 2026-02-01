# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["ResourceQueryParams", "QueryParams"]


class ResourceQueryParams(TypedDict, total=False):
    query: Required[str]

    folder_id: Annotated[str, PropertyInfo(alias="folderId")]

    folder_name: Annotated[str, PropertyInfo(alias="folderName")]

    query_params: Annotated[QueryParams, PropertyInfo(alias="queryParams")]

    resources: SequenceNotStr[str]


class QueryParams(TypedDict, total=False):
    max_token_for_global_context: Annotated[float, PropertyInfo(alias="maxTokenForGlobalContext")]

    max_token_for_local_context: Annotated[float, PropertyInfo(alias="maxTokenForLocalContext")]

    max_token_for_text_unit: Annotated[float, PropertyInfo(alias="maxTokenForTextUnit")]

    mode: str

    only_need_context: Annotated[bool, PropertyInfo(alias="onlyNeedContext")]

    only_need_prompt: Annotated[bool, PropertyInfo(alias="onlyNeedPrompt")]

    response_type: Annotated[str, PropertyInfo(alias="responseType")]

    stream: bool

    top_k: Annotated[float, PropertyInfo(alias="topK")]

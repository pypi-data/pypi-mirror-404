# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["FileCreateParams"]


class FileCreateParams(TypedDict, total=False):
    file_name: Required[Annotated[str, PropertyInfo(alias="fileName")]]

    mime_type: Required[Annotated[str, PropertyInfo(alias="mimeType")]]

    name: Required[str]

    s3_file_path: Required[Annotated[str, PropertyInfo(alias="s3FilePath")]]

    size: Required[float]

    folder_id: Annotated[str, PropertyInfo(alias="folderId")]

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["Resource"]


class Resource(BaseModel):
    id: str

    rag_type: Literal["FILE", "WEBPAGE", "SITEMAP"] = FieldInfo(alias="ragType")

    file_name: Optional[str] = FieldInfo(alias="fileName", default=None)

    folder_id: Optional[str] = FieldInfo(alias="folderId", default=None)

    graph_status: Optional[object] = FieldInfo(alias="graphStatus", default=None)

    image_s3_file_path: Optional[str] = FieldInfo(alias="imageS3FilePath", default=None)

    key: Optional[str] = None

    last_updated: Optional[datetime] = FieldInfo(alias="lastUpdated", default=None)

    mime_type: Optional[str] = FieldInfo(alias="mimeType", default=None)

    num_scrolls: Optional[int] = FieldInfo(alias="numScrolls", default=None)

    processing_error: Optional[str] = FieldInfo(alias="processingError", default=None)

    raw_link: Optional[str] = FieldInfo(alias="rawLink", default=None)

    s3_file_path: Optional[str] = FieldInfo(alias="s3FilePath", default=None)

    signed_s3_file_path: Optional[str] = FieldInfo(alias="signedS3FilePath", default=None)

    size: Optional[int] = None

    status: Optional[Literal["STARTED", "PROCESSING", "FAILED", "AVAILABLE", "DELETED"]] = None

    update_frequency: Optional[str] = FieldInfo(alias="updateFrequency", default=None)

    uploaded_at: Optional[datetime] = FieldInfo(alias="uploadedAt", default=None)

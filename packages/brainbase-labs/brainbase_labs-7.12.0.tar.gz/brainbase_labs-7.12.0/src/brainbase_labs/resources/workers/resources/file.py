# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
import mimetypes

import httpx

from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.shared.resource import Resource
from ....types.workers.resources import file_create_params
from ....types.workers.resources.file_list_response import FileListResponse

__all__ = ["FileResource", "AsyncFileResource"]


class FileResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> FileResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return FileResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> FileResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return FileResourceWithStreamingResponse(self)

    def create(
        self,
        worker_id: str,
        *,
        local_file_path: str,
        name: str,
        folder_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Resource:
        """
        Create a new file resource by uploading a local file.

        This method performs the following steps:
          1. Reads the specified local file and determines its file name, MIME type, and size.
          2. Retrieves a signed upload URL from the upload service.
          3. Uploads the file to S3 using the signed URL.
          4. Makes the final API request with the file metadata.

        Args:
          local_file_path: The path to the local file to be uploaded.
          name: The name of the file resource.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")

        if not os.path.exists(local_file_path):
            raise ValueError(f"File does not exist: {local_file_path}")

        # Extract file details from the local file.
        file_name = os.path.basename(local_file_path)
        file_size = os.path.getsize(local_file_path)
        mime_type, _ = mimetypes.guess_type(local_file_path)
        if mime_type is None:
            mime_type = "application/octet-stream"
            
        # Get the base URL from environment variable
        base_url = os.getenv("BRAINBASE_S3_SIGNED_URL_BASE_URL", "https://brainbase-monorepo.onrender.com")

        # Step 1: Get the signed upload URL using self._get.
        # Use a relative URL so that self._get uses your client's base URL.
        upload_endpoint = f"{base_url}/api/upload/{worker_id}/resource-upload-url"
        params = {"fileName": file_name, "contentType": mime_type}
        upload_headers = {"x-api-key": "sk_8a2307bd1a63e3025ad348b7237b6335cd62951d499183133e2362d4e4a7"}

        http_timeout: float | httpx.Timeout | None = timeout if not isinstance(timeout, NotGiven) else 1000
        response = httpx.get(
            upload_endpoint,
            headers=upload_headers,
            params=params,
            timeout=http_timeout
        )
        response.raise_for_status()  # Raises an exception for HTTP errors
        upload_data = response.json()
        signed_upload_url = upload_data["uploadUrl"]

        # Step 2: Upload the file to S3 using the signed URL.
        with open(local_file_path, "rb") as f:
            file_content = f.read()
        put_headers = {"Content-Type": mime_type}
        put_response = httpx.put(signed_upload_url, content=file_content, headers=put_headers)
        put_response.raise_for_status()

        # Extract the S3 file path (without query parameters) to be stored.
        s3_file_path = signed_upload_url.split("?")[0]
        return self._post(
            f"/api/workers/{worker_id}/resources/file",
            body=maybe_transform(
                {
                    "file_name": file_name,
                    "mime_type": mime_type,
                    "name": name,
                    "s3_file_path": s3_file_path,
                    "size": file_size,
                    "folder_id": folder_id,
                },
                file_create_params.FileCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Resource,
        )

    def list(
        self,
        worker_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> FileListResponse:
        """
        Get all file resources for a worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return self._get(
            f"/api/workers/{worker_id}/resources/file",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=FileListResponse,
        )


class AsyncFileResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncFileResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncFileResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncFileResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncFileResourceWithStreamingResponse(self)

    async def create(
        self,
        worker_id: str,
        *,
        local_file_path: str,
        name: str,
        folder_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Resource:
        """
        Create a new file resource by uploading a local file.

        This method performs the following steps:
          1. Reads the specified local file and determines its file name, MIME type, and size.
          2. Retrieves a signed upload URL from the upload service.
          3. Uploads the file to S3 using the signed URL.
          4. Makes the final API request with the file metadata.

        Args:
          local_file_path: The path to the local file to be uploaded.
          name: The name of the file resource.
          extra_headers: Send extra headers.
          extra_query: Add additional query parameters to the request.
          extra_body: Add additional JSON properties to the request.
          timeout: Override the client-level default timeout for this request, in seconds.
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")

        if not os.path.exists(local_file_path):
            raise ValueError(f"File does not exist: {local_file_path}")

        # Extract file details from the local file.
        file_name = os.path.basename(local_file_path)
        file_size = os.path.getsize(local_file_path)
        mime_type, _ = mimetypes.guess_type(local_file_path)
        if mime_type is None:
            mime_type = "application/octet-stream"
            
        base_url = os.getenv("BRAINBASE_S3_SIGNED_URL_BASE_URL", "https://brainbase-monorepo.onrender.com")

        # Step 1: Get the signed upload URL using self._get.
        # Use a relative URL so that self._get uses your client's base URL.
        upload_endpoint = f"{base_url}/api/upload/{worker_id}/resource-upload-url"
        params = {"fileName": file_name, "contentType": mime_type}
        upload_headers = {"x-api-key": "sk_8a2307bd1a63e3025ad348b7237b6335cd62951d499183133e2362d4e4a7"}

        http_timeout: float | httpx.Timeout | None = timeout if not isinstance(timeout, NotGiven) else 1000
        response = httpx.get(
            upload_endpoint,
            headers=upload_headers,
            params=params,
            timeout=http_timeout
        )
        response.raise_for_status()  # Raises an exception for HTTP errors
        upload_data = response.json()
        signed_upload_url = upload_data["uploadUrl"]

        # Step 2: Upload the file to S3 using the signed URL.
        with open(local_file_path, "rb") as f:
            file_content = f.read()
        put_headers = {"Content-Type": mime_type}
        put_response = httpx.put(signed_upload_url, content=file_content, headers=put_headers)
        put_response.raise_for_status()

        # Extract the S3 file path (without query parameters) to be stored.
        s3_file_path = signed_upload_url.split("?")[0]
        return await self._post(
            f"/api/workers/{worker_id}/resources/file",
            body=await async_maybe_transform(
                {
                    "file_name": file_name,
                    "mime_type": mime_type,
                    "name": name,
                    "s3_file_path": s3_file_path,
                    "size": file_size,
                    "folder_id": folder_id,
                },
                file_create_params.FileCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Resource,
        )

    async def list(
        self,
        worker_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> FileListResponse:
        """
        Get all file resources for a worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return await self._get(
            f"/api/workers/{worker_id}/resources/file",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=FileListResponse,
        )


class FileResourceWithRawResponse:
    def __init__(self, file: FileResource) -> None:
        self._file = file

        self.create = to_raw_response_wrapper(
            file.create,
        )
        self.list = to_raw_response_wrapper(
            file.list,
        )


class AsyncFileResourceWithRawResponse:
    def __init__(self, file: AsyncFileResource) -> None:
        self._file = file

        self.create = async_to_raw_response_wrapper(
            file.create,
        )
        self.list = async_to_raw_response_wrapper(
            file.list,
        )


class FileResourceWithStreamingResponse:
    def __init__(self, file: FileResource) -> None:
        self._file = file

        self.create = to_streamed_response_wrapper(
            file.create,
        )
        self.list = to_streamed_response_wrapper(
            file.list,
        )


class AsyncFileResourceWithStreamingResponse:
    def __init__(self, file: AsyncFileResource) -> None:
        self._file = file

        self.create = async_to_streamed_response_wrapper(
            file.create,
        )
        self.list = async_to_streamed_response_wrapper(
            file.list,
        )

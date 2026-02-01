# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from .file import (
    FileResource,
    AsyncFileResource,
    FileResourceWithRawResponse,
    AsyncFileResourceWithRawResponse,
    FileResourceWithStreamingResponse,
    AsyncFileResourceWithStreamingResponse,
)
from .link import (
    LinkResource,
    AsyncLinkResource,
    LinkResourceWithRawResponse,
    AsyncLinkResourceWithRawResponse,
    LinkResourceWithStreamingResponse,
    AsyncLinkResourceWithStreamingResponse,
)
from ...._types import Body, Omit, Query, Headers, NoneType, NotGiven, SequenceNotStr, omit, not_given
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
from ....types.workers import resource_move_params, resource_query_params
from ....types.shared.resource import Resource
from ....types.workers.resource_query_response import ResourceQueryResponse

__all__ = ["ResourcesResource", "AsyncResourcesResource"]


class ResourcesResource(SyncAPIResource):
    @cached_property
    def link(self) -> LinkResource:
        return LinkResource(self._client)

    @cached_property
    def file(self) -> FileResource:
        return FileResource(self._client)

    @cached_property
    def with_raw_response(self) -> ResourcesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return ResourcesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ResourcesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return ResourcesResourceWithStreamingResponse(self)

    def retrieve(
        self,
        resource_id: str,
        *,
        worker_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Resource:
        """
        Get a single resource (link or file) details

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not resource_id:
            raise ValueError(f"Expected a non-empty value for `resource_id` but received {resource_id!r}")
        return self._get(
            f"/api/workers/{worker_id}/resources/{resource_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Resource,
        )

    def delete(
        self,
        resource_id: str,
        *,
        worker_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a resource (link or file)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not resource_id:
            raise ValueError(f"Expected a non-empty value for `resource_id` but received {resource_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/api/workers/{worker_id}/resources/{resource_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def move(
        self,
        resource_id: str,
        *,
        worker_id: str,
        folder_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Resource:
        """
        Move a resource to a different folder

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not resource_id:
            raise ValueError(f"Expected a non-empty value for `resource_id` but received {resource_id!r}")
        return self._post(
            f"/api/workers/{worker_id}/resources/{resource_id}/move",
            body=maybe_transform({"folder_id": folder_id}, resource_move_params.ResourceMoveParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Resource,
        )

    def query(
        self,
        worker_id: str,
        *,
        query: str,
        folder_id: str | Omit = omit,
        folder_name: str | Omit = omit,
        query_params: resource_query_params.QueryParams | Omit = omit,
        resources: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ResourceQueryResponse:
        """
        Query RAG resources using vector search

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return self._post(
            f"/api/workers/{worker_id}/resources/query",
            body=maybe_transform(
                {
                    "query": query,
                    "folder_id": folder_id,
                    "folder_name": folder_name,
                    "query_params": query_params,
                    "resources": resources,
                },
                resource_query_params.ResourceQueryParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ResourceQueryResponse,
        )


class AsyncResourcesResource(AsyncAPIResource):
    @cached_property
    def link(self) -> AsyncLinkResource:
        return AsyncLinkResource(self._client)

    @cached_property
    def file(self) -> AsyncFileResource:
        return AsyncFileResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncResourcesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncResourcesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncResourcesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncResourcesResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        resource_id: str,
        *,
        worker_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Resource:
        """
        Get a single resource (link or file) details

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not resource_id:
            raise ValueError(f"Expected a non-empty value for `resource_id` but received {resource_id!r}")
        return await self._get(
            f"/api/workers/{worker_id}/resources/{resource_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Resource,
        )

    async def delete(
        self,
        resource_id: str,
        *,
        worker_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a resource (link or file)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not resource_id:
            raise ValueError(f"Expected a non-empty value for `resource_id` but received {resource_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/api/workers/{worker_id}/resources/{resource_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def move(
        self,
        resource_id: str,
        *,
        worker_id: str,
        folder_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Resource:
        """
        Move a resource to a different folder

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not resource_id:
            raise ValueError(f"Expected a non-empty value for `resource_id` but received {resource_id!r}")
        return await self._post(
            f"/api/workers/{worker_id}/resources/{resource_id}/move",
            body=await async_maybe_transform({"folder_id": folder_id}, resource_move_params.ResourceMoveParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Resource,
        )

    async def query(
        self,
        worker_id: str,
        *,
        query: str,
        folder_id: str | Omit = omit,
        folder_name: str | Omit = omit,
        query_params: resource_query_params.QueryParams | Omit = omit,
        resources: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ResourceQueryResponse:
        """
        Query RAG resources using vector search

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return await self._post(
            f"/api/workers/{worker_id}/resources/query",
            body=await async_maybe_transform(
                {
                    "query": query,
                    "folder_id": folder_id,
                    "folder_name": folder_name,
                    "query_params": query_params,
                    "resources": resources,
                },
                resource_query_params.ResourceQueryParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ResourceQueryResponse,
        )


class ResourcesResourceWithRawResponse:
    def __init__(self, resources: ResourcesResource) -> None:
        self._resources = resources

        self.retrieve = to_raw_response_wrapper(
            resources.retrieve,
        )
        self.delete = to_raw_response_wrapper(
            resources.delete,
        )
        self.move = to_raw_response_wrapper(
            resources.move,
        )
        self.query = to_raw_response_wrapper(
            resources.query,
        )

    @cached_property
    def link(self) -> LinkResourceWithRawResponse:
        return LinkResourceWithRawResponse(self._resources.link)

    @cached_property
    def file(self) -> FileResourceWithRawResponse:
        return FileResourceWithRawResponse(self._resources.file)


class AsyncResourcesResourceWithRawResponse:
    def __init__(self, resources: AsyncResourcesResource) -> None:
        self._resources = resources

        self.retrieve = async_to_raw_response_wrapper(
            resources.retrieve,
        )
        self.delete = async_to_raw_response_wrapper(
            resources.delete,
        )
        self.move = async_to_raw_response_wrapper(
            resources.move,
        )
        self.query = async_to_raw_response_wrapper(
            resources.query,
        )

    @cached_property
    def link(self) -> AsyncLinkResourceWithRawResponse:
        return AsyncLinkResourceWithRawResponse(self._resources.link)

    @cached_property
    def file(self) -> AsyncFileResourceWithRawResponse:
        return AsyncFileResourceWithRawResponse(self._resources.file)


class ResourcesResourceWithStreamingResponse:
    def __init__(self, resources: ResourcesResource) -> None:
        self._resources = resources

        self.retrieve = to_streamed_response_wrapper(
            resources.retrieve,
        )
        self.delete = to_streamed_response_wrapper(
            resources.delete,
        )
        self.move = to_streamed_response_wrapper(
            resources.move,
        )
        self.query = to_streamed_response_wrapper(
            resources.query,
        )

    @cached_property
    def link(self) -> LinkResourceWithStreamingResponse:
        return LinkResourceWithStreamingResponse(self._resources.link)

    @cached_property
    def file(self) -> FileResourceWithStreamingResponse:
        return FileResourceWithStreamingResponse(self._resources.file)


class AsyncResourcesResourceWithStreamingResponse:
    def __init__(self, resources: AsyncResourcesResource) -> None:
        self._resources = resources

        self.retrieve = async_to_streamed_response_wrapper(
            resources.retrieve,
        )
        self.delete = async_to_streamed_response_wrapper(
            resources.delete,
        )
        self.move = async_to_streamed_response_wrapper(
            resources.move,
        )
        self.query = async_to_streamed_response_wrapper(
            resources.query,
        )

    @cached_property
    def link(self) -> AsyncLinkResourceWithStreamingResponse:
        return AsyncLinkResourceWithStreamingResponse(self._resources.link)

    @cached_property
    def file(self) -> AsyncFileResourceWithStreamingResponse:
        return AsyncFileResourceWithStreamingResponse(self._resources.file)

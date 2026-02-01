# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

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
from ....types.workers.resources import link_create_params
from ....types.workers.resources.link_list_response import LinkListResponse

__all__ = ["LinkResource", "AsyncLinkResource"]


class LinkResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> LinkResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return LinkResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> LinkResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return LinkResourceWithStreamingResponse(self)

    def create(
        self,
        worker_id: str,
        *,
        name: str,
        raw_link: str,
        update_frequency: str,
        folder_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Resource:
        """
        Create a new link resource

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return self._post(
            f"/api/workers/{worker_id}/resources/link",
            body=maybe_transform(
                {
                    "name": name,
                    "raw_link": raw_link,
                    "update_frequency": update_frequency,
                    "folder_id": folder_id,
                },
                link_create_params.LinkCreateParams,
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
    ) -> LinkListResponse:
        """
        Get all link resources for a worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return self._get(
            f"/api/workers/{worker_id}/resources/link",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LinkListResponse,
        )


class AsyncLinkResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncLinkResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncLinkResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncLinkResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncLinkResourceWithStreamingResponse(self)

    async def create(
        self,
        worker_id: str,
        *,
        name: str,
        raw_link: str,
        update_frequency: str,
        folder_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Resource:
        """
        Create a new link resource

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return await self._post(
            f"/api/workers/{worker_id}/resources/link",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "raw_link": raw_link,
                    "update_frequency": update_frequency,
                    "folder_id": folder_id,
                },
                link_create_params.LinkCreateParams,
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
    ) -> LinkListResponse:
        """
        Get all link resources for a worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return await self._get(
            f"/api/workers/{worker_id}/resources/link",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LinkListResponse,
        )


class LinkResourceWithRawResponse:
    def __init__(self, link: LinkResource) -> None:
        self._link = link

        self.create = to_raw_response_wrapper(
            link.create,
        )
        self.list = to_raw_response_wrapper(
            link.list,
        )


class AsyncLinkResourceWithRawResponse:
    def __init__(self, link: AsyncLinkResource) -> None:
        self._link = link

        self.create = async_to_raw_response_wrapper(
            link.create,
        )
        self.list = async_to_raw_response_wrapper(
            link.list,
        )


class LinkResourceWithStreamingResponse:
    def __init__(self, link: LinkResource) -> None:
        self._link = link

        self.create = to_streamed_response_wrapper(
            link.create,
        )
        self.list = to_streamed_response_wrapper(
            link.list,
        )


class AsyncLinkResourceWithStreamingResponse:
    def __init__(self, link: AsyncLinkResource) -> None:
        self._link = link

        self.create = async_to_streamed_response_wrapper(
            link.create,
        )
        self.list = async_to_streamed_response_wrapper(
            link.list,
        )

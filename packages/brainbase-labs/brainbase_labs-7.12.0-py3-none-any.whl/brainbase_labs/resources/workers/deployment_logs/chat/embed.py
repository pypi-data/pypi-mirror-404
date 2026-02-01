# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ....._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ....._utils import maybe_transform, async_maybe_transform
from ....._compat import cached_property
from ....._resource import SyncAPIResource, AsyncAPIResource
from ....._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ....._base_client import make_request_options
from .....types.workers.deployment_logs.chat import embed_list_params
from .....types.workers.deployment_logs.chat.embed_list_response import EmbedListResponse
from .....types.workers.deployment_logs.chat.embed_retrieve_response import EmbedRetrieveResponse

__all__ = ["EmbedResource", "AsyncEmbedResource"]


class EmbedResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> EmbedResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return EmbedResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> EmbedResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return EmbedResourceWithStreamingResponse(self)

    def retrieve(
        self,
        log_id: str,
        *,
        worker_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmbedRetrieveResponse:
        """
        Retrieve a single chat embed deployment log record

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not log_id:
            raise ValueError(f"Expected a non-empty value for `log_id` but received {log_id!r}")
        return self._get(
            f"/api/workers/{worker_id}/deploymentLogs/chat-embed/{log_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmbedRetrieveResponse,
        )

    def list(
        self,
        worker_id: str,
        *,
        deployment_id: str | Omit = omit,
        flow_id: str | Omit = omit,
        session_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmbedListResponse:
        """Retrieves all chat embed deployment logs for the worker.

        Optionally, logs can be
        filtered by deploymentId and/or flowId by providing corresponding query
        parameters.

        Args:
          deployment_id: Filter logs by deployment id

          flow_id: Filter logs by flow id

          session_id: Filter logs by session id

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return self._get(
            f"/api/workers/{worker_id}/deploymentLogs/chat-embed",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "deployment_id": deployment_id,
                        "flow_id": flow_id,
                        "session_id": session_id,
                    },
                    embed_list_params.EmbedListParams,
                ),
            ),
            cast_to=EmbedListResponse,
        )


class AsyncEmbedResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncEmbedResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncEmbedResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncEmbedResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncEmbedResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        log_id: str,
        *,
        worker_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmbedRetrieveResponse:
        """
        Retrieve a single chat embed deployment log record

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not log_id:
            raise ValueError(f"Expected a non-empty value for `log_id` but received {log_id!r}")
        return await self._get(
            f"/api/workers/{worker_id}/deploymentLogs/chat-embed/{log_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmbedRetrieveResponse,
        )

    async def list(
        self,
        worker_id: str,
        *,
        deployment_id: str | Omit = omit,
        flow_id: str | Omit = omit,
        session_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmbedListResponse:
        """Retrieves all chat embed deployment logs for the worker.

        Optionally, logs can be
        filtered by deploymentId and/or flowId by providing corresponding query
        parameters.

        Args:
          deployment_id: Filter logs by deployment id

          flow_id: Filter logs by flow id

          session_id: Filter logs by session id

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return await self._get(
            f"/api/workers/{worker_id}/deploymentLogs/chat-embed",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "deployment_id": deployment_id,
                        "flow_id": flow_id,
                        "session_id": session_id,
                    },
                    embed_list_params.EmbedListParams,
                ),
            ),
            cast_to=EmbedListResponse,
        )


class EmbedResourceWithRawResponse:
    def __init__(self, embed: EmbedResource) -> None:
        self._embed = embed

        self.retrieve = to_raw_response_wrapper(
            embed.retrieve,
        )
        self.list = to_raw_response_wrapper(
            embed.list,
        )


class AsyncEmbedResourceWithRawResponse:
    def __init__(self, embed: AsyncEmbedResource) -> None:
        self._embed = embed

        self.retrieve = async_to_raw_response_wrapper(
            embed.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            embed.list,
        )


class EmbedResourceWithStreamingResponse:
    def __init__(self, embed: EmbedResource) -> None:
        self._embed = embed

        self.retrieve = to_streamed_response_wrapper(
            embed.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            embed.list,
        )


class AsyncEmbedResourceWithStreamingResponse:
    def __init__(self, embed: AsyncEmbedResource) -> None:
        self._embed = embed

        self.retrieve = async_to_streamed_response_wrapper(
            embed.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            embed.list,
        )

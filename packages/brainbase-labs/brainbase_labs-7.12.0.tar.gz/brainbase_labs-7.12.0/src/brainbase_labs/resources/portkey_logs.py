# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import portkey_log_create_params
from .._types import Body, Query, Headers, NoneType, NotGiven, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options

__all__ = ["PortkeyLogsResource", "AsyncPortkeyLogsResource"]


class PortkeyLogsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PortkeyLogsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return PortkeyLogsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PortkeyLogsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return PortkeyLogsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        body: object,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Receive logs from Portkey webhook

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/portkey-logs",
            body=maybe_transform(body, portkey_log_create_params.PortkeyLogCreateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncPortkeyLogsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPortkeyLogsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncPortkeyLogsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPortkeyLogsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncPortkeyLogsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        body: object,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Receive logs from Portkey webhook

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/portkey-logs",
            body=await async_maybe_transform(body, portkey_log_create_params.PortkeyLogCreateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class PortkeyLogsResourceWithRawResponse:
    def __init__(self, portkey_logs: PortkeyLogsResource) -> None:
        self._portkey_logs = portkey_logs

        self.create = to_raw_response_wrapper(
            portkey_logs.create,
        )


class AsyncPortkeyLogsResourceWithRawResponse:
    def __init__(self, portkey_logs: AsyncPortkeyLogsResource) -> None:
        self._portkey_logs = portkey_logs

        self.create = async_to_raw_response_wrapper(
            portkey_logs.create,
        )


class PortkeyLogsResourceWithStreamingResponse:
    def __init__(self, portkey_logs: PortkeyLogsResource) -> None:
        self._portkey_logs = portkey_logs

        self.create = to_streamed_response_wrapper(
            portkey_logs.create,
        )


class AsyncPortkeyLogsResourceWithStreamingResponse:
    def __init__(self, portkey_logs: AsyncPortkeyLogsResource) -> None:
        self._portkey_logs = portkey_logs

        self.create = async_to_streamed_response_wrapper(
            portkey_logs.create,
        )

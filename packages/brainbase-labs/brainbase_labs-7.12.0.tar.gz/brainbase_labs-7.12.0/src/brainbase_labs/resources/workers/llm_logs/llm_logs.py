# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .by_call import (
    ByCallResource,
    AsyncByCallResource,
    ByCallResourceWithRawResponse,
    AsyncByCallResourceWithRawResponse,
    ByCallResourceWithStreamingResponse,
    AsyncByCallResourceWithStreamingResponse,
)
from ...._types import Body, Omit, Query, Headers, NoneType, NotGiven, omit, not_given
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
from ....types.workers import llm_log_list_params
from ....types.workers.llm_log_list_response import LlmLogListResponse
from ....types.workers.llm_logs.by_session_list_response import BySessionListResponse

__all__ = ["LlmLogsResource", "AsyncLlmLogsResource"]


class LlmLogsResource(SyncAPIResource):
    @cached_property
    def by_call(self) -> ByCallResource:
        return ByCallResource(self._client)

    @cached_property
    def with_raw_response(self) -> LlmLogsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return LlmLogsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> LlmLogsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return LlmLogsResourceWithStreamingResponse(self)

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
    ) -> None:
        """
        Get a specific LLM log

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
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._get(
            f"/api/workers/{worker_id}/llm-logs/{log_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def list(
        self,
        worker_id: str,
        *,
        call_id: str | Omit = omit,
        event_type: str | Omit = omit,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        session_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LlmLogListResponse:
        """
        List LLM logs for a team

        Args:
          call_id: Filter by call ID

          event_type: Filter by event type (beforeRequestHook, afterRequestHook)

          limit: Number of logs to return

          offset: Offset for pagination

          session_id: Filter by session ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return self._get(
            f"/api/workers/{worker_id}/llm-logs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "call_id": call_id,
                        "event_type": event_type,
                        "limit": limit,
                        "offset": offset,
                        "session_id": session_id,
                    },
                    llm_log_list_params.LlmLogListParams,
                ),
            ),
            cast_to=LlmLogListResponse,
        )

    def delete(
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
    ) -> None:
        """
        Delete an LLM log

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
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/api/workers/{worker_id}/llm-logs/{log_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def get_by_session(
        self,
        session_id: str,
        *,
        worker_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BySessionListResponse:
        """
        Get all LLM logs for a specific session

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._get(
            f"/api/workers/{worker_id}/llm-logs/by-session/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BySessionListResponse,
        )


class AsyncLlmLogsResource(AsyncAPIResource):
    @cached_property
    def by_call(self) -> AsyncByCallResource:
        return AsyncByCallResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncLlmLogsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncLlmLogsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncLlmLogsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncLlmLogsResourceWithStreamingResponse(self)

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
    ) -> None:
        """
        Get a specific LLM log

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
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._get(
            f"/api/workers/{worker_id}/llm-logs/{log_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def list(
        self,
        worker_id: str,
        *,
        call_id: str | Omit = omit,
        event_type: str | Omit = omit,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        session_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LlmLogListResponse:
        """
        List LLM logs for a team

        Args:
          call_id: Filter by call ID

          event_type: Filter by event type (beforeRequestHook, afterRequestHook)

          limit: Number of logs to return

          offset: Offset for pagination

          session_id: Filter by session ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return await self._get(
            f"/api/workers/{worker_id}/llm-logs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "call_id": call_id,
                        "event_type": event_type,
                        "limit": limit,
                        "offset": offset,
                        "session_id": session_id,
                    },
                    llm_log_list_params.LlmLogListParams,
                ),
            ),
            cast_to=LlmLogListResponse,
        )

    async def delete(
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
    ) -> None:
        """
        Delete an LLM log

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
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/api/workers/{worker_id}/llm-logs/{log_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def get_by_session(
        self,
        session_id: str,
        *,
        worker_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BySessionListResponse:
        """
        Get all LLM logs for a specific session

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._get(
            f"/api/workers/{worker_id}/llm-logs/by-session/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BySessionListResponse,
        )


class LlmLogsResourceWithRawResponse:
    def __init__(self, llm_logs: LlmLogsResource) -> None:
        self._llm_logs = llm_logs

        self.retrieve = to_raw_response_wrapper(
            llm_logs.retrieve,
        )
        self.list = to_raw_response_wrapper(
            llm_logs.list,
        )
        self.delete = to_raw_response_wrapper(
            llm_logs.delete,
        )
        self.get_by_session = to_raw_response_wrapper(
            llm_logs.get_by_session,
        )

    @cached_property
    def by_call(self) -> ByCallResourceWithRawResponse:
        return ByCallResourceWithRawResponse(self._llm_logs.by_call)


class AsyncLlmLogsResourceWithRawResponse:
    def __init__(self, llm_logs: AsyncLlmLogsResource) -> None:
        self._llm_logs = llm_logs

        self.retrieve = async_to_raw_response_wrapper(
            llm_logs.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            llm_logs.list,
        )
        self.delete = async_to_raw_response_wrapper(
            llm_logs.delete,
        )
        self.get_by_session = async_to_raw_response_wrapper(
            llm_logs.get_by_session,
        )

    @cached_property
    def by_call(self) -> AsyncByCallResourceWithRawResponse:
        return AsyncByCallResourceWithRawResponse(self._llm_logs.by_call)


class LlmLogsResourceWithStreamingResponse:
    def __init__(self, llm_logs: LlmLogsResource) -> None:
        self._llm_logs = llm_logs

        self.retrieve = to_streamed_response_wrapper(
            llm_logs.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            llm_logs.list,
        )
        self.delete = to_streamed_response_wrapper(
            llm_logs.delete,
        )
        self.get_by_session = to_streamed_response_wrapper(
            llm_logs.get_by_session,
        )

    @cached_property
    def by_call(self) -> ByCallResourceWithStreamingResponse:
        return ByCallResourceWithStreamingResponse(self._llm_logs.by_call)


class AsyncLlmLogsResourceWithStreamingResponse:
    def __init__(self, llm_logs: AsyncLlmLogsResource) -> None:
        self._llm_logs = llm_logs

        self.retrieve = async_to_streamed_response_wrapper(
            llm_logs.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            llm_logs.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            llm_logs.delete,
        )
        self.get_by_session = async_to_streamed_response_wrapper(
            llm_logs.get_by_session,
        )

    @cached_property
    def by_call(self) -> AsyncByCallResourceWithStreamingResponse:
        return AsyncByCallResourceWithStreamingResponse(self._llm_logs.by_call)

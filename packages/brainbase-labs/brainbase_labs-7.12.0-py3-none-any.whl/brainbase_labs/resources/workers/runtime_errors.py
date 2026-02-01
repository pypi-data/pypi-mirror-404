# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ..._types import Body, Omit, Query, Headers, NoneType, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.workers import runtime_error_list_params, runtime_error_record_params

__all__ = ["RuntimeErrorsResource", "AsyncRuntimeErrorsResource"]


class RuntimeErrorsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> RuntimeErrorsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return RuntimeErrorsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RuntimeErrorsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return RuntimeErrorsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        error_id: str,
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
        Get a specific runtime error

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not error_id:
            raise ValueError(f"Expected a non-empty value for `error_id` but received {error_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._get(
            f"/api/workers/{worker_id}/runtime-errors/{error_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def list(
        self,
        worker_id: str,
        *,
        deployment_id: str | Omit = omit,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        service: str | Omit = omit,
        severity: str | Omit = omit,
        type: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        List runtime errors for a worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._get(
            f"/api/workers/{worker_id}/runtime-errors",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "deployment_id": deployment_id,
                        "limit": limit,
                        "offset": offset,
                        "service": service,
                        "severity": severity,
                        "type": type,
                    },
                    runtime_error_list_params.RuntimeErrorListParams,
                ),
            ),
            cast_to=NoneType,
        )

    def record(
        self,
        worker_id: str,
        *,
        error: str,
        service: str,
        type: str,
        bb_engine_session_id: str | Omit = omit,
        deployment_id: str | Omit = omit,
        flow_id: str | Omit = omit,
        function_name: str | Omit = omit,
        line_number: int | Omit = omit,
        metadata: object | Omit = omit,
        severity: Literal["warning", "error", "critical"] | Omit = omit,
        traceback: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Record a runtime error from the Based engine

        Args:
          error: Error message

          service: Service that generated the error (e.g., "based_engine", "sms")

          type: Error type/class (e.g., "ValueError", "RuntimeError")

          bb_engine_session_id: Session ID for trace correlation

          deployment_id: Deployment ID (optional)

          flow_id: Flow ID (used to lookup deployment if deploymentId not provided)

          function_name: Function being executed when error occurred

          line_number: Line number in Based code

          metadata: Additional context

          traceback: Full stack trace

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            f"/api/workers/{worker_id}/runtime-errors",
            body=maybe_transform(
                {
                    "error": error,
                    "service": service,
                    "type": type,
                    "bb_engine_session_id": bb_engine_session_id,
                    "deployment_id": deployment_id,
                    "flow_id": flow_id,
                    "function_name": function_name,
                    "line_number": line_number,
                    "metadata": metadata,
                    "severity": severity,
                    "traceback": traceback,
                },
                runtime_error_record_params.RuntimeErrorRecordParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncRuntimeErrorsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncRuntimeErrorsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncRuntimeErrorsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRuntimeErrorsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncRuntimeErrorsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        error_id: str,
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
        Get a specific runtime error

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not error_id:
            raise ValueError(f"Expected a non-empty value for `error_id` but received {error_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._get(
            f"/api/workers/{worker_id}/runtime-errors/{error_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def list(
        self,
        worker_id: str,
        *,
        deployment_id: str | Omit = omit,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        service: str | Omit = omit,
        severity: str | Omit = omit,
        type: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        List runtime errors for a worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._get(
            f"/api/workers/{worker_id}/runtime-errors",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "deployment_id": deployment_id,
                        "limit": limit,
                        "offset": offset,
                        "service": service,
                        "severity": severity,
                        "type": type,
                    },
                    runtime_error_list_params.RuntimeErrorListParams,
                ),
            ),
            cast_to=NoneType,
        )

    async def record(
        self,
        worker_id: str,
        *,
        error: str,
        service: str,
        type: str,
        bb_engine_session_id: str | Omit = omit,
        deployment_id: str | Omit = omit,
        flow_id: str | Omit = omit,
        function_name: str | Omit = omit,
        line_number: int | Omit = omit,
        metadata: object | Omit = omit,
        severity: Literal["warning", "error", "critical"] | Omit = omit,
        traceback: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Record a runtime error from the Based engine

        Args:
          error: Error message

          service: Service that generated the error (e.g., "based_engine", "sms")

          type: Error type/class (e.g., "ValueError", "RuntimeError")

          bb_engine_session_id: Session ID for trace correlation

          deployment_id: Deployment ID (optional)

          flow_id: Flow ID (used to lookup deployment if deploymentId not provided)

          function_name: Function being executed when error occurred

          line_number: Line number in Based code

          metadata: Additional context

          traceback: Full stack trace

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            f"/api/workers/{worker_id}/runtime-errors",
            body=await async_maybe_transform(
                {
                    "error": error,
                    "service": service,
                    "type": type,
                    "bb_engine_session_id": bb_engine_session_id,
                    "deployment_id": deployment_id,
                    "flow_id": flow_id,
                    "function_name": function_name,
                    "line_number": line_number,
                    "metadata": metadata,
                    "severity": severity,
                    "traceback": traceback,
                },
                runtime_error_record_params.RuntimeErrorRecordParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class RuntimeErrorsResourceWithRawResponse:
    def __init__(self, runtime_errors: RuntimeErrorsResource) -> None:
        self._runtime_errors = runtime_errors

        self.retrieve = to_raw_response_wrapper(
            runtime_errors.retrieve,
        )
        self.list = to_raw_response_wrapper(
            runtime_errors.list,
        )
        self.record = to_raw_response_wrapper(
            runtime_errors.record,
        )


class AsyncRuntimeErrorsResourceWithRawResponse:
    def __init__(self, runtime_errors: AsyncRuntimeErrorsResource) -> None:
        self._runtime_errors = runtime_errors

        self.retrieve = async_to_raw_response_wrapper(
            runtime_errors.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            runtime_errors.list,
        )
        self.record = async_to_raw_response_wrapper(
            runtime_errors.record,
        )


class RuntimeErrorsResourceWithStreamingResponse:
    def __init__(self, runtime_errors: RuntimeErrorsResource) -> None:
        self._runtime_errors = runtime_errors

        self.retrieve = to_streamed_response_wrapper(
            runtime_errors.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            runtime_errors.list,
        )
        self.record = to_streamed_response_wrapper(
            runtime_errors.record,
        )


class AsyncRuntimeErrorsResourceWithStreamingResponse:
    def __init__(self, runtime_errors: AsyncRuntimeErrorsResource) -> None:
        self._runtime_errors = runtime_errors

        self.retrieve = async_to_streamed_response_wrapper(
            runtime_errors.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            runtime_errors.list,
        )
        self.record = async_to_streamed_response_wrapper(
            runtime_errors.record,
        )

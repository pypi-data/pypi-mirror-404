# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

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
from ....types.workers.deployments import default_check_update_params

__all__ = ["DefaultChecksResource", "AsyncDefaultChecksResource"]


class DefaultChecksResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> DefaultChecksResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return DefaultChecksResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DefaultChecksResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return DefaultChecksResourceWithStreamingResponse(self)

    def retrieve(
        self,
        deployment_id: str,
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
        Get resolved default checks configuration for a deployment

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not deployment_id:
            raise ValueError(f"Expected a non-empty value for `deployment_id` but received {deployment_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._get(
            f"/api/workers/{worker_id}/deployments/{deployment_id}/default-checks",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def update(
        self,
        deployment_id: str,
        *,
        worker_id: str,
        ai_enabled: bool | Omit = omit,
        ai_threshold: float | Omit = omit,
        alert_emails: SequenceNotStr[str] | Omit = omit,
        api_enabled: bool | Omit = omit,
        api_threshold: float | Omit = omit,
        enabled: bool | Omit = omit,
        latency_enabled: bool | Omit = omit,
        latency_threshold: float | Omit = omit,
        sample_rate: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Create or update deployment-level default checks overrides

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not deployment_id:
            raise ValueError(f"Expected a non-empty value for `deployment_id` but received {deployment_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._put(
            f"/api/workers/{worker_id}/deployments/{deployment_id}/default-checks",
            body=maybe_transform(
                {
                    "ai_enabled": ai_enabled,
                    "ai_threshold": ai_threshold,
                    "alert_emails": alert_emails,
                    "api_enabled": api_enabled,
                    "api_threshold": api_threshold,
                    "enabled": enabled,
                    "latency_enabled": latency_enabled,
                    "latency_threshold": latency_threshold,
                    "sample_rate": sample_rate,
                },
                default_check_update_params.DefaultCheckUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def delete(
        self,
        deployment_id: str,
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
        Remove deployment-level overrides (revert to team defaults)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not deployment_id:
            raise ValueError(f"Expected a non-empty value for `deployment_id` but received {deployment_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/api/workers/{worker_id}/deployments/{deployment_id}/default-checks",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncDefaultChecksResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncDefaultChecksResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncDefaultChecksResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDefaultChecksResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncDefaultChecksResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        deployment_id: str,
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
        Get resolved default checks configuration for a deployment

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not deployment_id:
            raise ValueError(f"Expected a non-empty value for `deployment_id` but received {deployment_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._get(
            f"/api/workers/{worker_id}/deployments/{deployment_id}/default-checks",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def update(
        self,
        deployment_id: str,
        *,
        worker_id: str,
        ai_enabled: bool | Omit = omit,
        ai_threshold: float | Omit = omit,
        alert_emails: SequenceNotStr[str] | Omit = omit,
        api_enabled: bool | Omit = omit,
        api_threshold: float | Omit = omit,
        enabled: bool | Omit = omit,
        latency_enabled: bool | Omit = omit,
        latency_threshold: float | Omit = omit,
        sample_rate: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Create or update deployment-level default checks overrides

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not deployment_id:
            raise ValueError(f"Expected a non-empty value for `deployment_id` but received {deployment_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._put(
            f"/api/workers/{worker_id}/deployments/{deployment_id}/default-checks",
            body=await async_maybe_transform(
                {
                    "ai_enabled": ai_enabled,
                    "ai_threshold": ai_threshold,
                    "alert_emails": alert_emails,
                    "api_enabled": api_enabled,
                    "api_threshold": api_threshold,
                    "enabled": enabled,
                    "latency_enabled": latency_enabled,
                    "latency_threshold": latency_threshold,
                    "sample_rate": sample_rate,
                },
                default_check_update_params.DefaultCheckUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def delete(
        self,
        deployment_id: str,
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
        Remove deployment-level overrides (revert to team defaults)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not deployment_id:
            raise ValueError(f"Expected a non-empty value for `deployment_id` but received {deployment_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/api/workers/{worker_id}/deployments/{deployment_id}/default-checks",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class DefaultChecksResourceWithRawResponse:
    def __init__(self, default_checks: DefaultChecksResource) -> None:
        self._default_checks = default_checks

        self.retrieve = to_raw_response_wrapper(
            default_checks.retrieve,
        )
        self.update = to_raw_response_wrapper(
            default_checks.update,
        )
        self.delete = to_raw_response_wrapper(
            default_checks.delete,
        )


class AsyncDefaultChecksResourceWithRawResponse:
    def __init__(self, default_checks: AsyncDefaultChecksResource) -> None:
        self._default_checks = default_checks

        self.retrieve = async_to_raw_response_wrapper(
            default_checks.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            default_checks.update,
        )
        self.delete = async_to_raw_response_wrapper(
            default_checks.delete,
        )


class DefaultChecksResourceWithStreamingResponse:
    def __init__(self, default_checks: DefaultChecksResource) -> None:
        self._default_checks = default_checks

        self.retrieve = to_streamed_response_wrapper(
            default_checks.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            default_checks.update,
        )
        self.delete = to_streamed_response_wrapper(
            default_checks.delete,
        )


class AsyncDefaultChecksResourceWithStreamingResponse:
    def __init__(self, default_checks: AsyncDefaultChecksResource) -> None:
        self._default_checks = default_checks

        self.retrieve = async_to_streamed_response_wrapper(
            default_checks.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            default_checks.update,
        )
        self.delete = async_to_streamed_response_wrapper(
            default_checks.delete,
        )

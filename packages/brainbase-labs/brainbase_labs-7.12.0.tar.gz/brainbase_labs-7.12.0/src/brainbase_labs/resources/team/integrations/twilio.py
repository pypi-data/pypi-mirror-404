# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

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
from ....types.team.integrations import twilio_create_params
from ....types.shared.integration import Integration

__all__ = ["TwilioResource", "AsyncTwilioResource"]


class TwilioResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> TwilioResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return TwilioResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TwilioResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return TwilioResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        account_sid: str,
        auth_token: str,
        description: str | Omit = omit,
        name: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Integration:
        """
        Create a new Twilio integration for the authenticated team.

        Args:
          auth_token: Provide the plain text auth token. It will be encrypted before being stored.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/team/integrations/twilio/create",
            body=maybe_transform(
                {
                    "account_sid": account_sid,
                    "auth_token": auth_token,
                    "description": description,
                    "name": name,
                },
                twilio_create_params.TwilioCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Integration,
        )

    def delete(
        self,
        integration_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete an existing Twilio integration.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not integration_id:
            raise ValueError(f"Expected a non-empty value for `integration_id` but received {integration_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/api/team/integrations/twilio/{integration_id}/delete",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncTwilioResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncTwilioResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncTwilioResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTwilioResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncTwilioResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        account_sid: str,
        auth_token: str,
        description: str | Omit = omit,
        name: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Integration:
        """
        Create a new Twilio integration for the authenticated team.

        Args:
          auth_token: Provide the plain text auth token. It will be encrypted before being stored.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/team/integrations/twilio/create",
            body=await async_maybe_transform(
                {
                    "account_sid": account_sid,
                    "auth_token": auth_token,
                    "description": description,
                    "name": name,
                },
                twilio_create_params.TwilioCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Integration,
        )

    async def delete(
        self,
        integration_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete an existing Twilio integration.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not integration_id:
            raise ValueError(f"Expected a non-empty value for `integration_id` but received {integration_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/api/team/integrations/twilio/{integration_id}/delete",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class TwilioResourceWithRawResponse:
    def __init__(self, twilio: TwilioResource) -> None:
        self._twilio = twilio

        self.create = to_raw_response_wrapper(
            twilio.create,
        )
        self.delete = to_raw_response_wrapper(
            twilio.delete,
        )


class AsyncTwilioResourceWithRawResponse:
    def __init__(self, twilio: AsyncTwilioResource) -> None:
        self._twilio = twilio

        self.create = async_to_raw_response_wrapper(
            twilio.create,
        )
        self.delete = async_to_raw_response_wrapper(
            twilio.delete,
        )


class TwilioResourceWithStreamingResponse:
    def __init__(self, twilio: TwilioResource) -> None:
        self._twilio = twilio

        self.create = to_streamed_response_wrapper(
            twilio.create,
        )
        self.delete = to_streamed_response_wrapper(
            twilio.delete,
        )


class AsyncTwilioResourceWithStreamingResponse:
    def __init__(self, twilio: AsyncTwilioResource) -> None:
        self._twilio = twilio

        self.create = async_to_streamed_response_wrapper(
            twilio.create,
        )
        self.delete = async_to_streamed_response_wrapper(
            twilio.delete,
        )

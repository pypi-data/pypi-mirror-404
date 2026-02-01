# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Query, Headers, NoneType, NotGiven, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...types.team import custom_voice_create_params
from ..._base_client import make_request_options

__all__ = ["CustomVoicesResource", "AsyncCustomVoicesResource"]


class CustomVoicesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CustomVoicesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return CustomVoicesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CustomVoicesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return CustomVoicesResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        elevenlabs_voice_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Add a custom ElevenLabs voice for the team

        Args:
          elevenlabs_voice_id: The ElevenLabs voice ID (name and owner are fetched automatically)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/api/team/customVoices",
            body=maybe_transform(
                {"elevenlabs_voice_id": elevenlabs_voice_id}, custom_voice_create_params.CustomVoiceCreateParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """Get all custom voices for the team"""
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._get(
            "/api/team/customVoices",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def delete(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a custom voice

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/api/team/customVoices/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncCustomVoicesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCustomVoicesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncCustomVoicesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCustomVoicesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncCustomVoicesResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        elevenlabs_voice_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Add a custom ElevenLabs voice for the team

        Args:
          elevenlabs_voice_id: The ElevenLabs voice ID (name and owner are fetched automatically)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/api/team/customVoices",
            body=await async_maybe_transform(
                {"elevenlabs_voice_id": elevenlabs_voice_id}, custom_voice_create_params.CustomVoiceCreateParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """Get all custom voices for the team"""
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._get(
            "/api/team/customVoices",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def delete(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a custom voice

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/api/team/customVoices/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class CustomVoicesResourceWithRawResponse:
    def __init__(self, custom_voices: CustomVoicesResource) -> None:
        self._custom_voices = custom_voices

        self.create = to_raw_response_wrapper(
            custom_voices.create,
        )
        self.list = to_raw_response_wrapper(
            custom_voices.list,
        )
        self.delete = to_raw_response_wrapper(
            custom_voices.delete,
        )


class AsyncCustomVoicesResourceWithRawResponse:
    def __init__(self, custom_voices: AsyncCustomVoicesResource) -> None:
        self._custom_voices = custom_voices

        self.create = async_to_raw_response_wrapper(
            custom_voices.create,
        )
        self.list = async_to_raw_response_wrapper(
            custom_voices.list,
        )
        self.delete = async_to_raw_response_wrapper(
            custom_voices.delete,
        )


class CustomVoicesResourceWithStreamingResponse:
    def __init__(self, custom_voices: CustomVoicesResource) -> None:
        self._custom_voices = custom_voices

        self.create = to_streamed_response_wrapper(
            custom_voices.create,
        )
        self.list = to_streamed_response_wrapper(
            custom_voices.list,
        )
        self.delete = to_streamed_response_wrapper(
            custom_voices.delete,
        )


class AsyncCustomVoicesResourceWithStreamingResponse:
    def __init__(self, custom_voices: AsyncCustomVoicesResource) -> None:
        self._custom_voices = custom_voices

        self.create = async_to_streamed_response_wrapper(
            custom_voices.create,
        )
        self.list = async_to_streamed_response_wrapper(
            custom_voices.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            custom_voices.delete,
        )

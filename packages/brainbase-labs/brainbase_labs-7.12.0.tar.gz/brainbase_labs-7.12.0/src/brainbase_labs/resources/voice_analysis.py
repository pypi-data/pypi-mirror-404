# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Literal

import httpx

from ..types import voice_analysis_analyze_params
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
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
from ..types.voice_analysis_analyze_response import VoiceAnalysisAnalyzeResponse

__all__ = ["VoiceAnalysisResource", "AsyncVoiceAnalysisResource"]


class VoiceAnalysisResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> VoiceAnalysisResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return VoiceAnalysisResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> VoiceAnalysisResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return VoiceAnalysisResourceWithStreamingResponse(self)

    def analyze(
        self,
        *,
        deployment_ids: SequenceNotStr[str] | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        granularity: Literal["daily", "weekly", "monthly", "yearly"] | Omit = omit,
        include_call_details: bool | Omit = omit,
        include_transfers: bool | Omit = omit,
        start_date: Union[str, datetime] | Omit = omit,
        timezone: str | Omit = omit,
        worker_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceAnalysisAnalyzeResponse:
        """
        Get detailed voice deployment analysis with billing breakdown

        Args:
          deployment_ids: Optional filter by deployment IDs

          end_date: End date for analysis (ISO 8601)

          granularity: Time granularity for breakdown

          include_call_details: Include detailed call logs in response

          include_transfers: Include transfer analysis

          start_date: Start date for analysis (ISO 8601)

          timezone: Timezone for date calculations

          worker_id: Optional filter by worker ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/voice-analysis",
            body=maybe_transform(
                {
                    "deployment_ids": deployment_ids,
                    "end_date": end_date,
                    "granularity": granularity,
                    "include_call_details": include_call_details,
                    "include_transfers": include_transfers,
                    "start_date": start_date,
                    "timezone": timezone,
                    "worker_id": worker_id,
                },
                voice_analysis_analyze_params.VoiceAnalysisAnalyzeParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceAnalysisAnalyzeResponse,
        )


class AsyncVoiceAnalysisResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncVoiceAnalysisResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncVoiceAnalysisResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncVoiceAnalysisResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncVoiceAnalysisResourceWithStreamingResponse(self)

    async def analyze(
        self,
        *,
        deployment_ids: SequenceNotStr[str] | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        granularity: Literal["daily", "weekly", "monthly", "yearly"] | Omit = omit,
        include_call_details: bool | Omit = omit,
        include_transfers: bool | Omit = omit,
        start_date: Union[str, datetime] | Omit = omit,
        timezone: str | Omit = omit,
        worker_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceAnalysisAnalyzeResponse:
        """
        Get detailed voice deployment analysis with billing breakdown

        Args:
          deployment_ids: Optional filter by deployment IDs

          end_date: End date for analysis (ISO 8601)

          granularity: Time granularity for breakdown

          include_call_details: Include detailed call logs in response

          include_transfers: Include transfer analysis

          start_date: Start date for analysis (ISO 8601)

          timezone: Timezone for date calculations

          worker_id: Optional filter by worker ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/voice-analysis",
            body=await async_maybe_transform(
                {
                    "deployment_ids": deployment_ids,
                    "end_date": end_date,
                    "granularity": granularity,
                    "include_call_details": include_call_details,
                    "include_transfers": include_transfers,
                    "start_date": start_date,
                    "timezone": timezone,
                    "worker_id": worker_id,
                },
                voice_analysis_analyze_params.VoiceAnalysisAnalyzeParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceAnalysisAnalyzeResponse,
        )


class VoiceAnalysisResourceWithRawResponse:
    def __init__(self, voice_analysis: VoiceAnalysisResource) -> None:
        self._voice_analysis = voice_analysis

        self.analyze = to_raw_response_wrapper(
            voice_analysis.analyze,
        )


class AsyncVoiceAnalysisResourceWithRawResponse:
    def __init__(self, voice_analysis: AsyncVoiceAnalysisResource) -> None:
        self._voice_analysis = voice_analysis

        self.analyze = async_to_raw_response_wrapper(
            voice_analysis.analyze,
        )


class VoiceAnalysisResourceWithStreamingResponse:
    def __init__(self, voice_analysis: VoiceAnalysisResource) -> None:
        self._voice_analysis = voice_analysis

        self.analyze = to_streamed_response_wrapper(
            voice_analysis.analyze,
        )


class AsyncVoiceAnalysisResourceWithStreamingResponse:
    def __init__(self, voice_analysis: AsyncVoiceAnalysisResource) -> None:
        self._voice_analysis = voice_analysis

        self.analyze = async_to_streamed_response_wrapper(
            voice_analysis.analyze,
        )

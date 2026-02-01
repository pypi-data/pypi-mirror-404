# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Literal

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
from ....types.shared.log import Log
from ....types.workers.deployment_logs import voice_list_params
from ....types.workers.deployment_logs.voice_list_response import VoiceListResponse

__all__ = ["VoiceResource", "AsyncVoiceResource"]


class VoiceResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> VoiceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return VoiceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> VoiceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return VoiceResourceWithStreamingResponse(self)

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
    ) -> Log:
        """
        Retrieve a single voice deployment log record

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
            f"/api/workers/{worker_id}/deploymentLogs/voice/{log_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Log,
        )

    def list(
        self,
        worker_id: str,
        *,
        call_sid: str | Omit = omit,
        deployment_id: str | Omit = omit,
        direction: Literal["inbound", "outbound"] | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        end_time_after: Union[str, datetime] | Omit = omit,
        end_time_before: Union[str, datetime] | Omit = omit,
        external_call_id: str | Omit = omit,
        flow_id: str | Omit = omit,
        from_number: str | Omit = omit,
        limit: int | Omit = omit,
        page: int | Omit = omit,
        search_query: str | Omit = omit,
        sort_by: Literal[
            "startTime",
            "endTime",
            "direction",
            "fromNumber",
            "toNumber",
            "status",
            "externalCallId",
            "createdAt",
            "updatedAt",
        ]
        | Omit = omit,
        sort_order: Literal["asc", "desc"] | Omit = omit,
        start_date: Union[str, datetime] | Omit = omit,
        start_time_after: Union[str, datetime] | Omit = omit,
        start_time_before: Union[str, datetime] | Omit = omit,
        status: str | Omit = omit,
        to_number: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceListResponse:
        """
        Retrieves voice deployment logs for the worker with comprehensive filtering and pagination support.

        Args:
          call_sid: Filter by Twilio call SID

          deployment_id: Filter logs by deployment id

          direction: Filter by call direction

          end_date: Deprecated - use startTimeBefore instead

          end_time_after: Filter logs with endTime after this date (ISO 8601 format)

          end_time_before: Filter logs with endTime before this date (ISO 8601 format)

          external_call_id: Filter by external call ID

          flow_id: Filter logs by flow id

          from_number: Filter by caller phone number (partial match)

          direction: Filter by call direction (inbound/outbound)

          from_number: Filter by caller phone number (partial match)

          to_number: Filter by called phone number (partial match)

          status: Filter by call status

          external_call_id: Filter by external call ID

          call_sid: Filter by Twilio call SID

          search_query: Search in call transcriptions (case-insensitive)

          start_time_after: Filter logs with startTime after this date (ISO 8601 format)

          start_time_before: Filter logs with startTime before this date (ISO 8601 format)

          end_time_after: Filter logs with endTime after this date (ISO 8601 format)

          end_time_before: Filter logs with endTime before this date (ISO 8601 format)

          start_date: Deprecated - use start_time_after instead

          end_date: Deprecated - use start_time_before instead

          sort_by: Field to sort by (startTime, endTime, direction, fromNumber, toNumber, status, externalCallId, createdAt, updatedAt)

          sort_order: Sort order (asc or desc)

          limit: Number of items per page (max 100)

          page: Page number for pagination

          search_query: Search in call transcriptions (case-insensitive)

          sort_by: Field to sort by

          sort_order: Sort order (ascending or descending)

          start_date: Deprecated - use startTimeAfter instead

          start_time_after: Filter logs with startTime after this date (ISO 8601 format)

          start_time_before: Filter logs with startTime before this date (ISO 8601 format)

          status: Filter by call status

          to_number: Filter by called phone number (partial match)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return self._get(
            f"/api/workers/{worker_id}/deploymentLogs/voice",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "call_sid": call_sid,
                        "deployment_id": deployment_id,
                        "direction": direction,
                        "end_date": end_date,
                        "end_time_after": end_time_after,
                        "end_time_before": end_time_before,
                        "external_call_id": external_call_id,
                        "flow_id": flow_id,
                        "from_number": from_number,
                        "direction": direction,
                        "from_number": from_number,
                        "to_number": to_number,
                        "status": status,
                        "external_call_id": external_call_id,
                        "call_sid": call_sid,
                        "search_query": search_query,
                        "start_time_after": start_time_after,
                        "start_time_before": start_time_before,
                        "end_time_after": end_time_after,
                        "end_time_before": end_time_before,
                        "start_date": start_date,
                        "end_date": end_date,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                        "limit": limit,
                        "page": page,
                        "search_query": search_query,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                        "start_date": start_date,
                        "start_time_after": start_time_after,
                        "start_time_before": start_time_before,
                        "status": status,
                        "to_number": to_number,
                    },
                    voice_list_params.VoiceListParams,
                ),
            ),
            cast_to=VoiceListResponse,
        )


class AsyncVoiceResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncVoiceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncVoiceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncVoiceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncVoiceResourceWithStreamingResponse(self)

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
    ) -> Log:
        """
        Retrieve a single voice deployment log record

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
            f"/api/workers/{worker_id}/deploymentLogs/voice/{log_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Log,
        )

    async def list(
        self,
        worker_id: str,
        *,
        call_sid: str | Omit = omit,
        deployment_id: str | Omit = omit,
        direction: Literal["inbound", "outbound"] | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        end_time_after: Union[str, datetime] | Omit = omit,
        end_time_before: Union[str, datetime] | Omit = omit,
        external_call_id: str | Omit = omit,
        flow_id: str | Omit = omit,
        from_number: str | Omit = omit,
        limit: int | Omit = omit,
        page: int | Omit = omit,
        search_query: str | Omit = omit,
        sort_by: Literal[
            "startTime",
            "endTime",
            "direction",
            "fromNumber",
            "toNumber",
            "status",
            "externalCallId",
            "createdAt",
            "updatedAt",
        ]
        | Omit = omit,
        sort_order: Literal["asc", "desc"] | Omit = omit,
        start_date: Union[str, datetime] | Omit = omit,
        start_time_after: Union[str, datetime] | Omit = omit,
        start_time_before: Union[str, datetime] | Omit = omit,
        status: str | Omit = omit,
        to_number: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceListResponse:
        """
        Retrieves voice deployment logs for the worker with comprehensive filtering and pagination support.

        Args:
          call_sid: Filter by Twilio call SID

          deployment_id: Filter logs by deployment id

          direction: Filter by call direction

          end_date: Deprecated - use startTimeBefore instead

          end_time_after: Filter logs with endTime after this date (ISO 8601 format)

          end_time_before: Filter logs with endTime before this date (ISO 8601 format)

          external_call_id: Filter by external call ID

          flow_id: Filter logs by flow id

          from_number: Filter by caller phone number (partial match)

          direction: Filter by call direction (inbound/outbound)

          from_number: Filter by caller phone number (partial match)

          to_number: Filter by called phone number (partial match)

          status: Filter by call status

          external_call_id: Filter by external call ID

          call_sid: Filter by Twilio call SID

          search_query: Search in call transcriptions (case-insensitive)

          start_time_after: Filter logs with startTime after this date (ISO 8601 format)

          start_time_before: Filter logs with startTime before this date (ISO 8601 format)

          end_time_after: Filter logs with endTime after this date (ISO 8601 format)

          end_time_before: Filter logs with endTime before this date (ISO 8601 format)

          start_date: Deprecated - use start_time_after instead

          end_date: Deprecated - use start_time_before instead

          sort_by: Field to sort by (startTime, endTime, direction, fromNumber, toNumber, status, externalCallId, createdAt, updatedAt)

          sort_order: Sort order (asc or desc)

          limit: Number of items per page (max 100)

          page: Page number for pagination

          search_query: Search in call transcriptions (case-insensitive)

          sort_by: Field to sort by

          sort_order: Sort order (ascending or descending)

          start_date: Deprecated - use startTimeAfter instead

          start_time_after: Filter logs with startTime after this date (ISO 8601 format)

          start_time_before: Filter logs with startTime before this date (ISO 8601 format)

          status: Filter by call status

          to_number: Filter by called phone number (partial match)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return await self._get(
            f"/api/workers/{worker_id}/deploymentLogs/voice",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "call_sid": call_sid,
                        "deployment_id": deployment_id,
                        "direction": direction,
                        "end_date": end_date,
                        "end_time_after": end_time_after,
                        "end_time_before": end_time_before,
                        "external_call_id": external_call_id,
                        "flow_id": flow_id,
                        "from_number": from_number,
                        "direction": direction,
                        "from_number": from_number,
                        "to_number": to_number,
                        "status": status,
                        "external_call_id": external_call_id,
                        "call_sid": call_sid,
                        "search_query": search_query,
                        "start_time_after": start_time_after,
                        "start_time_before": start_time_before,
                        "end_time_after": end_time_after,
                        "end_time_before": end_time_before,
                        "start_date": start_date,
                        "end_date": end_date,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                        "limit": limit,
                        "page": page,
                        "search_query": search_query,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                        "start_date": start_date,
                        "start_time_after": start_time_after,
                        "start_time_before": start_time_before,
                        "status": status,
                        "to_number": to_number,
                    },
                    voice_list_params.VoiceListParams,
                ),
            ),
            cast_to=VoiceListResponse,
        )


class VoiceResourceWithRawResponse:
    def __init__(self, voice: VoiceResource) -> None:
        self._voice = voice

        self.retrieve = to_raw_response_wrapper(
            voice.retrieve,
        )
        self.list = to_raw_response_wrapper(
            voice.list,
        )


class AsyncVoiceResourceWithRawResponse:
    def __init__(self, voice: AsyncVoiceResource) -> None:
        self._voice = voice

        self.retrieve = async_to_raw_response_wrapper(
            voice.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            voice.list,
        )


class VoiceResourceWithStreamingResponse:
    def __init__(self, voice: VoiceResource) -> None:
        self._voice = voice

        self.retrieve = to_streamed_response_wrapper(
            voice.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            voice.list,
        )


class AsyncVoiceResourceWithStreamingResponse:
    def __init__(self, voice: AsyncVoiceResource) -> None:
        self._voice = voice

        self.retrieve = async_to_streamed_response_wrapper(
            voice.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            voice.list,
        )

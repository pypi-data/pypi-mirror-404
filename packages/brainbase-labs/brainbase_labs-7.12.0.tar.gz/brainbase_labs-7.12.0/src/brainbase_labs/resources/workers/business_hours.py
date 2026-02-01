# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict

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
from ...types.workers import (
    business_hour_list_params,
    business_hour_create_params,
    business_hour_update_params,
    business_hour_retrieve_params,
)
from ...types.workers.business_hour_list_response import BusinessHourListResponse
from ...types.workers.business_hour_create_response import BusinessHourCreateResponse
from ...types.workers.business_hour_update_response import BusinessHourUpdateResponse
from ...types.workers.business_hour_retrieve_response import BusinessHourRetrieveResponse

__all__ = ["BusinessHoursResource", "AsyncBusinessHoursResource"]


class BusinessHoursResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> BusinessHoursResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return BusinessHoursResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> BusinessHoursResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return BusinessHoursResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        hours: Dict[str, str],
        primary_tag: str | Omit = omit,
        secondary_tag: str | Omit = omit,
        timezone: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BusinessHourCreateResponse:
        """
        Create new business hours

        Args:
          hours: JSON object containing business hours configuration

          primary_tag: Primary tag for categorization (e.g., business name, location)

          secondary_tag: Secondary tag for categorization (e.g., department, type)

          timezone: Timezone for the business hours (e.g., 'America/New_York', 'UTC',
              'Europe/London')

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/workers/business-hours",
            body=maybe_transform(
                {
                    "hours": hours,
                    "primary_tag": primary_tag,
                    "secondary_tag": secondary_tag,
                    "timezone": timezone,
                },
                business_hour_create_params.BusinessHourCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BusinessHourCreateResponse,
        )

    def retrieve(
        self,
        id: str,
        *,
        include_team_phone_hours: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BusinessHourRetrieveResponse:
        """
        Get business hours by ID

        Args:
          include_team_phone_hours: Set to true to include related team phone hours

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/api/workers/business-hours/{id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"include_team_phone_hours": include_team_phone_hours},
                    business_hour_retrieve_params.BusinessHourRetrieveParams,
                ),
            ),
            cast_to=BusinessHourRetrieveResponse,
        )

    def update(
        self,
        id: str,
        *,
        hours: Dict[str, str] | Omit = omit,
        primary_tag: str | Omit = omit,
        secondary_tag: str | Omit = omit,
        timezone: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BusinessHourUpdateResponse:
        """
        Update business hours

        Args:
          hours: JSON object containing business hours configuration

          primary_tag: Primary tag for categorization (e.g., business name, location)

          secondary_tag: Secondary tag for categorization (e.g., department, type)

          timezone: Timezone for the business hours (e.g., 'America/New_York', 'UTC',
              'Europe/London')

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._put(
            f"/api/workers/business-hours/{id}",
            body=maybe_transform(
                {
                    "hours": hours,
                    "primary_tag": primary_tag,
                    "secondary_tag": secondary_tag,
                    "timezone": timezone,
                },
                business_hour_update_params.BusinessHourUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BusinessHourUpdateResponse,
        )

    def list(
        self,
        *,
        include_team_phone_hours: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BusinessHourListResponse:
        """
        Get all business hours

        Args:
          include_team_phone_hours: Set to true to include related team phone hours

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/api/workers/business-hours",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"include_team_phone_hours": include_team_phone_hours},
                    business_hour_list_params.BusinessHourListParams,
                ),
            ),
            cast_to=BusinessHourListResponse,
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
        Delete business hours

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
            f"/api/workers/business-hours/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncBusinessHoursResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncBusinessHoursResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncBusinessHoursResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncBusinessHoursResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncBusinessHoursResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        hours: Dict[str, str],
        primary_tag: str | Omit = omit,
        secondary_tag: str | Omit = omit,
        timezone: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BusinessHourCreateResponse:
        """
        Create new business hours

        Args:
          hours: JSON object containing business hours configuration

          primary_tag: Primary tag for categorization (e.g., business name, location)

          secondary_tag: Secondary tag for categorization (e.g., department, type)

          timezone: Timezone for the business hours (e.g., 'America/New_York', 'UTC',
              'Europe/London')

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/workers/business-hours",
            body=await async_maybe_transform(
                {
                    "hours": hours,
                    "primary_tag": primary_tag,
                    "secondary_tag": secondary_tag,
                    "timezone": timezone,
                },
                business_hour_create_params.BusinessHourCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BusinessHourCreateResponse,
        )

    async def retrieve(
        self,
        id: str,
        *,
        include_team_phone_hours: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BusinessHourRetrieveResponse:
        """
        Get business hours by ID

        Args:
          include_team_phone_hours: Set to true to include related team phone hours

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/api/workers/business-hours/{id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"include_team_phone_hours": include_team_phone_hours},
                    business_hour_retrieve_params.BusinessHourRetrieveParams,
                ),
            ),
            cast_to=BusinessHourRetrieveResponse,
        )

    async def update(
        self,
        id: str,
        *,
        hours: Dict[str, str] | Omit = omit,
        primary_tag: str | Omit = omit,
        secondary_tag: str | Omit = omit,
        timezone: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BusinessHourUpdateResponse:
        """
        Update business hours

        Args:
          hours: JSON object containing business hours configuration

          primary_tag: Primary tag for categorization (e.g., business name, location)

          secondary_tag: Secondary tag for categorization (e.g., department, type)

          timezone: Timezone for the business hours (e.g., 'America/New_York', 'UTC',
              'Europe/London')

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._put(
            f"/api/workers/business-hours/{id}",
            body=await async_maybe_transform(
                {
                    "hours": hours,
                    "primary_tag": primary_tag,
                    "secondary_tag": secondary_tag,
                    "timezone": timezone,
                },
                business_hour_update_params.BusinessHourUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BusinessHourUpdateResponse,
        )

    async def list(
        self,
        *,
        include_team_phone_hours: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BusinessHourListResponse:
        """
        Get all business hours

        Args:
          include_team_phone_hours: Set to true to include related team phone hours

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/api/workers/business-hours",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"include_team_phone_hours": include_team_phone_hours},
                    business_hour_list_params.BusinessHourListParams,
                ),
            ),
            cast_to=BusinessHourListResponse,
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
        Delete business hours

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
            f"/api/workers/business-hours/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class BusinessHoursResourceWithRawResponse:
    def __init__(self, business_hours: BusinessHoursResource) -> None:
        self._business_hours = business_hours

        self.create = to_raw_response_wrapper(
            business_hours.create,
        )
        self.retrieve = to_raw_response_wrapper(
            business_hours.retrieve,
        )
        self.update = to_raw_response_wrapper(
            business_hours.update,
        )
        self.list = to_raw_response_wrapper(
            business_hours.list,
        )
        self.delete = to_raw_response_wrapper(
            business_hours.delete,
        )


class AsyncBusinessHoursResourceWithRawResponse:
    def __init__(self, business_hours: AsyncBusinessHoursResource) -> None:
        self._business_hours = business_hours

        self.create = async_to_raw_response_wrapper(
            business_hours.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            business_hours.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            business_hours.update,
        )
        self.list = async_to_raw_response_wrapper(
            business_hours.list,
        )
        self.delete = async_to_raw_response_wrapper(
            business_hours.delete,
        )


class BusinessHoursResourceWithStreamingResponse:
    def __init__(self, business_hours: BusinessHoursResource) -> None:
        self._business_hours = business_hours

        self.create = to_streamed_response_wrapper(
            business_hours.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            business_hours.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            business_hours.update,
        )
        self.list = to_streamed_response_wrapper(
            business_hours.list,
        )
        self.delete = to_streamed_response_wrapper(
            business_hours.delete,
        )


class AsyncBusinessHoursResourceWithStreamingResponse:
    def __init__(self, business_hours: AsyncBusinessHoursResource) -> None:
        self._business_hours = business_hours

        self.create = async_to_streamed_response_wrapper(
            business_hours.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            business_hours.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            business_hours.update,
        )
        self.list = async_to_streamed_response_wrapper(
            business_hours.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            business_hours.delete,
        )

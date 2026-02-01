# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

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
    team_phone_hour_list_params,
    team_phone_hour_create_params,
    team_phone_hour_update_params,
    team_phone_hour_retrieve_params,
)
from ...types.workers.team_phone_hour_list_response import TeamPhoneHourListResponse
from ...types.workers.team_phone_hour_create_response import TeamPhoneHourCreateResponse
from ...types.workers.team_phone_hour_update_response import TeamPhoneHourUpdateResponse
from ...types.workers.team_phone_hour_retrieve_response import TeamPhoneHourRetrieveResponse

__all__ = ["TeamPhoneHoursResource", "AsyncTeamPhoneHoursResource"]


class TeamPhoneHoursResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> TeamPhoneHoursResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return TeamPhoneHoursResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TeamPhoneHoursResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return TeamPhoneHoursResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        hours_id: str,
        phone_number: str,
        team_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TeamPhoneHourCreateResponse:
        """
        Create new team phone hours

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/workers/team-phone-hours",
            body=maybe_transform(
                {
                    "hours_id": hours_id,
                    "phone_number": phone_number,
                    "team_id": team_id,
                },
                team_phone_hour_create_params.TeamPhoneHourCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TeamPhoneHourCreateResponse,
        )

    def retrieve(
        self,
        id: str,
        *,
        include_relations: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TeamPhoneHourRetrieveResponse:
        """
        Get team phone hours by ID

        Args:
          include_relations: Set to true to include related business hours and team

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/api/workers/team-phone-hours/{id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"include_relations": include_relations},
                    team_phone_hour_retrieve_params.TeamPhoneHourRetrieveParams,
                ),
            ),
            cast_to=TeamPhoneHourRetrieveResponse,
        )

    def update(
        self,
        id: str,
        *,
        hours_id: str | Omit = omit,
        phone_number: str | Omit = omit,
        team_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TeamPhoneHourUpdateResponse:
        """
        Update team phone hours

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._put(
            f"/api/workers/team-phone-hours/{id}",
            body=maybe_transform(
                {
                    "hours_id": hours_id,
                    "phone_number": phone_number,
                    "team_id": team_id,
                },
                team_phone_hour_update_params.TeamPhoneHourUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TeamPhoneHourUpdateResponse,
        )

    def list(
        self,
        *,
        include_relations: bool | Omit = omit,
        phone_number: str | Omit = omit,
        team_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TeamPhoneHourListResponse:
        """
        Get all team phone hours

        Args:
          include_relations: Set to true to include related business hours and team

          phone_number: Filter by phone number

          team_id: Filter by team ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/api/workers/team-phone-hours",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "include_relations": include_relations,
                        "phone_number": phone_number,
                        "team_id": team_id,
                    },
                    team_phone_hour_list_params.TeamPhoneHourListParams,
                ),
            ),
            cast_to=TeamPhoneHourListResponse,
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
        Delete team phone hours

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
            f"/api/workers/team-phone-hours/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncTeamPhoneHoursResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncTeamPhoneHoursResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncTeamPhoneHoursResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTeamPhoneHoursResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncTeamPhoneHoursResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        hours_id: str,
        phone_number: str,
        team_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TeamPhoneHourCreateResponse:
        """
        Create new team phone hours

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/workers/team-phone-hours",
            body=await async_maybe_transform(
                {
                    "hours_id": hours_id,
                    "phone_number": phone_number,
                    "team_id": team_id,
                },
                team_phone_hour_create_params.TeamPhoneHourCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TeamPhoneHourCreateResponse,
        )

    async def retrieve(
        self,
        id: str,
        *,
        include_relations: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TeamPhoneHourRetrieveResponse:
        """
        Get team phone hours by ID

        Args:
          include_relations: Set to true to include related business hours and team

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/api/workers/team-phone-hours/{id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"include_relations": include_relations},
                    team_phone_hour_retrieve_params.TeamPhoneHourRetrieveParams,
                ),
            ),
            cast_to=TeamPhoneHourRetrieveResponse,
        )

    async def update(
        self,
        id: str,
        *,
        hours_id: str | Omit = omit,
        phone_number: str | Omit = omit,
        team_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TeamPhoneHourUpdateResponse:
        """
        Update team phone hours

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._put(
            f"/api/workers/team-phone-hours/{id}",
            body=await async_maybe_transform(
                {
                    "hours_id": hours_id,
                    "phone_number": phone_number,
                    "team_id": team_id,
                },
                team_phone_hour_update_params.TeamPhoneHourUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TeamPhoneHourUpdateResponse,
        )

    async def list(
        self,
        *,
        include_relations: bool | Omit = omit,
        phone_number: str | Omit = omit,
        team_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TeamPhoneHourListResponse:
        """
        Get all team phone hours

        Args:
          include_relations: Set to true to include related business hours and team

          phone_number: Filter by phone number

          team_id: Filter by team ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/api/workers/team-phone-hours",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "include_relations": include_relations,
                        "phone_number": phone_number,
                        "team_id": team_id,
                    },
                    team_phone_hour_list_params.TeamPhoneHourListParams,
                ),
            ),
            cast_to=TeamPhoneHourListResponse,
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
        Delete team phone hours

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
            f"/api/workers/team-phone-hours/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class TeamPhoneHoursResourceWithRawResponse:
    def __init__(self, team_phone_hours: TeamPhoneHoursResource) -> None:
        self._team_phone_hours = team_phone_hours

        self.create = to_raw_response_wrapper(
            team_phone_hours.create,
        )
        self.retrieve = to_raw_response_wrapper(
            team_phone_hours.retrieve,
        )
        self.update = to_raw_response_wrapper(
            team_phone_hours.update,
        )
        self.list = to_raw_response_wrapper(
            team_phone_hours.list,
        )
        self.delete = to_raw_response_wrapper(
            team_phone_hours.delete,
        )


class AsyncTeamPhoneHoursResourceWithRawResponse:
    def __init__(self, team_phone_hours: AsyncTeamPhoneHoursResource) -> None:
        self._team_phone_hours = team_phone_hours

        self.create = async_to_raw_response_wrapper(
            team_phone_hours.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            team_phone_hours.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            team_phone_hours.update,
        )
        self.list = async_to_raw_response_wrapper(
            team_phone_hours.list,
        )
        self.delete = async_to_raw_response_wrapper(
            team_phone_hours.delete,
        )


class TeamPhoneHoursResourceWithStreamingResponse:
    def __init__(self, team_phone_hours: TeamPhoneHoursResource) -> None:
        self._team_phone_hours = team_phone_hours

        self.create = to_streamed_response_wrapper(
            team_phone_hours.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            team_phone_hours.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            team_phone_hours.update,
        )
        self.list = to_streamed_response_wrapper(
            team_phone_hours.list,
        )
        self.delete = to_streamed_response_wrapper(
            team_phone_hours.delete,
        )


class AsyncTeamPhoneHoursResourceWithStreamingResponse:
    def __init__(self, team_phone_hours: AsyncTeamPhoneHoursResource) -> None:
        self._team_phone_hours = team_phone_hours

        self.create = async_to_streamed_response_wrapper(
            team_phone_hours.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            team_phone_hours.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            team_phone_hours.update,
        )
        self.list = async_to_streamed_response_wrapper(
            team_phone_hours.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            team_phone_hours.delete,
        )

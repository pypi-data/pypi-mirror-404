# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal

import httpx

from ....._types import Body, Omit, Query, Headers, NoneType, NotGiven, omit, not_given
from ....._utils import maybe_transform, async_maybe_transform
from ....._compat import cached_property
from ....._resource import SyncAPIResource, AsyncAPIResource
from ....._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ....._base_client import make_request_options
from .....types.workers.deployments.voice import outbound_campaign_create_params, outbound_campaign_update_params
from .....types.workers.deployments.voice.outbound_campaign_list_response import OutboundCampaignListResponse
from .....types.workers.deployments.voice.outbound_campaign_create_response import OutboundCampaignCreateResponse
from .....types.workers.deployments.voice.outbound_campaign_update_response import OutboundCampaignUpdateResponse
from .....types.workers.deployments.voice.outbound_campaign_retrieve_response import OutboundCampaignRetrieveResponse

__all__ = ["OutboundCampaignsResource", "AsyncOutboundCampaignsResource"]


class OutboundCampaignsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> OutboundCampaignsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return OutboundCampaignsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> OutboundCampaignsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return OutboundCampaignsResourceWithStreamingResponse(self)

    def create(
        self,
        deployment_id: str,
        *,
        worker_id: str,
        data: Iterable[object],
        additional_data: object | Omit = omit,
        batch_interval_minutes: int | Omit = omit,
        batch_size: int | Omit = omit,
        created_by: str | Omit = omit,
        description: str | Omit = omit,
        flow_id: str | Omit = omit,
        name: str | Omit = omit,
        status: Literal["CREATED", "STARTED", "RUNNING", "COMPLETED", "STOPPED", "FAILED"] | Omit = omit,
        team_id: str | Omit = omit,
        telephony_provider: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OutboundCampaignCreateResponse:
        """
        Create a new outbound campaign

        Args:
          data: Contact data array

          additional_data: Additional metadata

          batch_interval_minutes: Minutes to wait between batches

          batch_size: Number of calls to make simultaneously

          created_by: User ID who created the campaign

          description: Campaign description

          flow_id: Flow ID

          name: Campaign name

          status: Campaign status

          team_id: Team ID

          telephony_provider: Telephony provider configuration

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not deployment_id:
            raise ValueError(f"Expected a non-empty value for `deployment_id` but received {deployment_id!r}")
        return self._post(
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}/outbound-campaigns",
            body=maybe_transform(
                {
                    "data": data,
                    "additional_data": additional_data,
                    "batch_interval_minutes": batch_interval_minutes,
                    "batch_size": batch_size,
                    "created_by": created_by,
                    "description": description,
                    "flow_id": flow_id,
                    "name": name,
                    "status": status,
                    "team_id": team_id,
                    "telephony_provider": telephony_provider,
                },
                outbound_campaign_create_params.OutboundCampaignCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OutboundCampaignCreateResponse,
        )

    def retrieve(
        self,
        campaign_id: str,
        *,
        worker_id: str,
        deployment_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OutboundCampaignRetrieveResponse:
        """
        Get a specific outbound campaign by ID

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
        if not campaign_id:
            raise ValueError(f"Expected a non-empty value for `campaign_id` but received {campaign_id!r}")
        return self._get(
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}/outbound-campaigns/{campaign_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OutboundCampaignRetrieveResponse,
        )

    def update(
        self,
        campaign_id: str,
        *,
        worker_id: str,
        deployment_id: str,
        additional_data: object | Omit = omit,
        batch_interval_minutes: int | Omit = omit,
        batch_size: int | Omit = omit,
        data: Iterable[object] | Omit = omit,
        description: str | Omit = omit,
        name: str | Omit = omit,
        status: Literal["CREATED", "STARTED", "RUNNING", "COMPLETED", "STOPPED", "FAILED"] | Omit = omit,
        telephony_provider: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OutboundCampaignUpdateResponse:
        """
        Update an outbound campaign

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
        if not campaign_id:
            raise ValueError(f"Expected a non-empty value for `campaign_id` but received {campaign_id!r}")
        return self._patch(
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}/outbound-campaigns/{campaign_id}",
            body=maybe_transform(
                {
                    "additional_data": additional_data,
                    "batch_interval_minutes": batch_interval_minutes,
                    "batch_size": batch_size,
                    "data": data,
                    "description": description,
                    "name": name,
                    "status": status,
                    "telephony_provider": telephony_provider,
                },
                outbound_campaign_update_params.OutboundCampaignUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OutboundCampaignUpdateResponse,
        )

    def list(
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
    ) -> OutboundCampaignListResponse:
        """
        Get all outbound campaigns for a voice deployment

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
        return self._get(
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}/outbound-campaigns",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OutboundCampaignListResponse,
        )

    def delete(
        self,
        campaign_id: str,
        *,
        worker_id: str,
        deployment_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete an outbound campaign

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
        if not campaign_id:
            raise ValueError(f"Expected a non-empty value for `campaign_id` but received {campaign_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}/outbound-campaigns/{campaign_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncOutboundCampaignsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncOutboundCampaignsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncOutboundCampaignsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncOutboundCampaignsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncOutboundCampaignsResourceWithStreamingResponse(self)

    async def create(
        self,
        deployment_id: str,
        *,
        worker_id: str,
        data: Iterable[object],
        additional_data: object | Omit = omit,
        batch_interval_minutes: int | Omit = omit,
        batch_size: int | Omit = omit,
        created_by: str | Omit = omit,
        description: str | Omit = omit,
        flow_id: str | Omit = omit,
        name: str | Omit = omit,
        status: Literal["CREATED", "STARTED", "RUNNING", "COMPLETED", "STOPPED", "FAILED"] | Omit = omit,
        team_id: str | Omit = omit,
        telephony_provider: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OutboundCampaignCreateResponse:
        """
        Create a new outbound campaign

        Args:
          data: Contact data array

          additional_data: Additional metadata

          batch_interval_minutes: Minutes to wait between batches

          batch_size: Number of calls to make simultaneously

          created_by: User ID who created the campaign

          description: Campaign description

          flow_id: Flow ID

          name: Campaign name

          status: Campaign status

          team_id: Team ID

          telephony_provider: Telephony provider configuration

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not deployment_id:
            raise ValueError(f"Expected a non-empty value for `deployment_id` but received {deployment_id!r}")
        return await self._post(
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}/outbound-campaigns",
            body=await async_maybe_transform(
                {
                    "data": data,
                    "additional_data": additional_data,
                    "batch_interval_minutes": batch_interval_minutes,
                    "batch_size": batch_size,
                    "created_by": created_by,
                    "description": description,
                    "flow_id": flow_id,
                    "name": name,
                    "status": status,
                    "team_id": team_id,
                    "telephony_provider": telephony_provider,
                },
                outbound_campaign_create_params.OutboundCampaignCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OutboundCampaignCreateResponse,
        )

    async def retrieve(
        self,
        campaign_id: str,
        *,
        worker_id: str,
        deployment_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OutboundCampaignRetrieveResponse:
        """
        Get a specific outbound campaign by ID

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
        if not campaign_id:
            raise ValueError(f"Expected a non-empty value for `campaign_id` but received {campaign_id!r}")
        return await self._get(
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}/outbound-campaigns/{campaign_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OutboundCampaignRetrieveResponse,
        )

    async def update(
        self,
        campaign_id: str,
        *,
        worker_id: str,
        deployment_id: str,
        additional_data: object | Omit = omit,
        batch_interval_minutes: int | Omit = omit,
        batch_size: int | Omit = omit,
        data: Iterable[object] | Omit = omit,
        description: str | Omit = omit,
        name: str | Omit = omit,
        status: Literal["CREATED", "STARTED", "RUNNING", "COMPLETED", "STOPPED", "FAILED"] | Omit = omit,
        telephony_provider: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OutboundCampaignUpdateResponse:
        """
        Update an outbound campaign

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
        if not campaign_id:
            raise ValueError(f"Expected a non-empty value for `campaign_id` but received {campaign_id!r}")
        return await self._patch(
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}/outbound-campaigns/{campaign_id}",
            body=await async_maybe_transform(
                {
                    "additional_data": additional_data,
                    "batch_interval_minutes": batch_interval_minutes,
                    "batch_size": batch_size,
                    "data": data,
                    "description": description,
                    "name": name,
                    "status": status,
                    "telephony_provider": telephony_provider,
                },
                outbound_campaign_update_params.OutboundCampaignUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OutboundCampaignUpdateResponse,
        )

    async def list(
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
    ) -> OutboundCampaignListResponse:
        """
        Get all outbound campaigns for a voice deployment

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
        return await self._get(
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}/outbound-campaigns",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OutboundCampaignListResponse,
        )

    async def delete(
        self,
        campaign_id: str,
        *,
        worker_id: str,
        deployment_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete an outbound campaign

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
        if not campaign_id:
            raise ValueError(f"Expected a non-empty value for `campaign_id` but received {campaign_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}/outbound-campaigns/{campaign_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class OutboundCampaignsResourceWithRawResponse:
    def __init__(self, outbound_campaigns: OutboundCampaignsResource) -> None:
        self._outbound_campaigns = outbound_campaigns

        self.create = to_raw_response_wrapper(
            outbound_campaigns.create,
        )
        self.retrieve = to_raw_response_wrapper(
            outbound_campaigns.retrieve,
        )
        self.update = to_raw_response_wrapper(
            outbound_campaigns.update,
        )
        self.list = to_raw_response_wrapper(
            outbound_campaigns.list,
        )
        self.delete = to_raw_response_wrapper(
            outbound_campaigns.delete,
        )


class AsyncOutboundCampaignsResourceWithRawResponse:
    def __init__(self, outbound_campaigns: AsyncOutboundCampaignsResource) -> None:
        self._outbound_campaigns = outbound_campaigns

        self.create = async_to_raw_response_wrapper(
            outbound_campaigns.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            outbound_campaigns.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            outbound_campaigns.update,
        )
        self.list = async_to_raw_response_wrapper(
            outbound_campaigns.list,
        )
        self.delete = async_to_raw_response_wrapper(
            outbound_campaigns.delete,
        )


class OutboundCampaignsResourceWithStreamingResponse:
    def __init__(self, outbound_campaigns: OutboundCampaignsResource) -> None:
        self._outbound_campaigns = outbound_campaigns

        self.create = to_streamed_response_wrapper(
            outbound_campaigns.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            outbound_campaigns.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            outbound_campaigns.update,
        )
        self.list = to_streamed_response_wrapper(
            outbound_campaigns.list,
        )
        self.delete = to_streamed_response_wrapper(
            outbound_campaigns.delete,
        )


class AsyncOutboundCampaignsResourceWithStreamingResponse:
    def __init__(self, outbound_campaigns: AsyncOutboundCampaignsResource) -> None:
        self._outbound_campaigns = outbound_campaigns

        self.create = async_to_streamed_response_wrapper(
            outbound_campaigns.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            outbound_campaigns.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            outbound_campaigns.update,
        )
        self.list = async_to_streamed_response_wrapper(
            outbound_campaigns.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            outbound_campaigns.delete,
        )

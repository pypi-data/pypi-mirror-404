# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable, Optional

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
from .custom_webhooks import (
    CustomWebhooksResource,
    AsyncCustomWebhooksResource,
    CustomWebhooksResourceWithRawResponse,
    AsyncCustomWebhooksResourceWithRawResponse,
    CustomWebhooksResourceWithStreamingResponse,
    AsyncCustomWebhooksResourceWithStreamingResponse,
)
from ....._base_client import make_request_options
from .outbound_campaigns import (
    OutboundCampaignsResource,
    AsyncOutboundCampaignsResource,
    OutboundCampaignsResourceWithRawResponse,
    AsyncOutboundCampaignsResourceWithRawResponse,
    OutboundCampaignsResourceWithStreamingResponse,
    AsyncOutboundCampaignsResourceWithStreamingResponse,
)
from .....types.workers.deployments import (
    voice_create_params,
    voice_update_params,
    voice_stop_campaign_params,
    voice_make_batch_calls_params,
)
from .....types.shared.voice_deployment import VoiceDeployment
from .....types.workers.deployments.voice_list_response import VoiceListResponse
from .....types.workers.deployments.voice_stop_campaign_response import VoiceStopCampaignResponse
from .....types.workers.deployments.voice_make_batch_calls_response import VoiceMakeBatchCallsResponse
from .....types.workers.deployments.voice_stop_batch_calls_response import VoiceStopBatchCallsResponse

__all__ = ["VoiceResource", "AsyncVoiceResource"]


class VoiceResource(SyncAPIResource):
    @cached_property
    def custom_webhooks(self) -> CustomWebhooksResource:
        return CustomWebhooksResource(self._client)

    @cached_property
    def outbound_campaigns(self) -> OutboundCampaignsResource:
        return OutboundCampaignsResource(self._client)

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

    def create(
        self,
        worker_id: str,
        *,
        flow_id: str,
        name: str,
        phone_number: str,
        backup_phone_message: str | Omit = omit,
        backup_phone_number: str | Omit = omit,
        enable_voice_sentiment: bool | Omit = omit,
        engine_model: Optional[str] | Omit = omit,
        external_config: voice_create_params.ExternalConfig | Omit = omit,
        extractions: Dict[str, voice_create_params.Extractions] | Omit = omit,
        success_criteria: Iterable[voice_create_params.SuccessCriterion] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceDeployment:
        """
        Create a new voice deployment

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return self._post(
            f"/api/workers/{worker_id}/deployments/voice",
            body=maybe_transform(
                {
                    "flow_id": flow_id,
                    "name": name,
                    "phone_number": phone_number,
                    "backup_phone_message": backup_phone_message,
                    "backup_phone_number": backup_phone_number,
                    "enable_voice_sentiment": enable_voice_sentiment,
                    "engine_model": engine_model,
                    "external_config": external_config,
                    "extractions": extractions,
                    "success_criteria": success_criteria,
                },
                voice_create_params.VoiceCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceDeployment,
        )

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
    ) -> VoiceDeployment:
        """
        Get a single voice deployment

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
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceDeployment,
        )

    def update(
        self,
        deployment_id: str,
        *,
        worker_id: str,
        backup_phone_message: str | Omit = omit,
        backup_phone_number: str | Omit = omit,
        custom_webhooks: Iterable[voice_update_params.CustomWebhook] | Omit = omit,
        enable_voice_sentiment: bool | Omit = omit,
        engine_model: Optional[str] | Omit = omit,
        external_config: voice_update_params.ExternalConfig | Omit = omit,
        extractions: Dict[str, voice_update_params.Extractions] | Omit = omit,
        flow_id: str | Omit = omit,
        name: str | Omit = omit,
        phone_number: str | Omit = omit,
        success_criteria: Iterable[voice_update_params.SuccessCriterion] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceDeployment:
        """
        Update a voice deployment

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
        return self._patch(
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}",
            body=maybe_transform(
                {
                    "backup_phone_message": backup_phone_message,
                    "backup_phone_number": backup_phone_number,
                    "custom_webhooks": custom_webhooks,
                    "enable_voice_sentiment": enable_voice_sentiment,
                    "engine_model": engine_model,
                    "external_config": external_config,
                    "extractions": extractions,
                    "flow_id": flow_id,
                    "name": name,
                    "phone_number": phone_number,
                    "success_criteria": success_criteria,
                },
                voice_update_params.VoiceUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceDeployment,
        )

    def list(
        self,
        worker_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceListResponse:
        """
        Get all voice deployments for a worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return self._get(
            f"/api/workers/{worker_id}/deployments/voice",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceListResponse,
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
        Delete a voice deployment

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
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def make_batch_calls(
        self,
        deployment_id: str,
        *,
        worker_id: str,
        data: Iterable[Dict[str, str]],
        additional_data: str | Omit = omit,
        batch_interval_minutes: float | Omit = omit,
        batch_size: float | Omit = omit,
        condition: Optional[str] | Omit = omit,
        country: str | Omit = omit,
        extractions: Optional[str] | Omit = omit,
        ws_url: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceMakeBatchCallsResponse:
        """
        Make batch calls for a voice deployment

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
        return self._post(
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}/make-batch-calls",
            body=maybe_transform(
                {
                    "data": data,
                    "additional_data": additional_data,
                    "batch_interval_minutes": batch_interval_minutes,
                    "batch_size": batch_size,
                    "condition": condition,
                    "country": country,
                    "extractions": extractions,
                    "ws_url": ws_url,
                },
                voice_make_batch_calls_params.VoiceMakeBatchCallsParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceMakeBatchCallsResponse,
        )

    def stop_batch_calls(
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
    ) -> VoiceStopBatchCallsResponse:
        """
        Removes all scheduled batch calls for the specified deployment from the queue
        and returns the removed items

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
        return self._post(
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}/stop-batch-calls",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceStopBatchCallsResponse,
        )

    def stop_campaign(
        self,
        deployment_id: str,
        *,
        worker_id: str,
        campaign_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceStopCampaignResponse:
        """
        Removes all scheduled calls for a specific campaign from the Redis queue

        Args:
          campaign_id: The campaign ID to stop

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
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}/stop-campaign",
            body=maybe_transform({"campaign_id": campaign_id}, voice_stop_campaign_params.VoiceStopCampaignParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceStopCampaignResponse,
        )


class AsyncVoiceResource(AsyncAPIResource):
    @cached_property
    def custom_webhooks(self) -> AsyncCustomWebhooksResource:
        return AsyncCustomWebhooksResource(self._client)

    @cached_property
    def outbound_campaigns(self) -> AsyncOutboundCampaignsResource:
        return AsyncOutboundCampaignsResource(self._client)

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

    async def create(
        self,
        worker_id: str,
        *,
        flow_id: str,
        name: str,
        phone_number: str,
        backup_phone_message: str | Omit = omit,
        backup_phone_number: str | Omit = omit,
        enable_voice_sentiment: bool | Omit = omit,
        engine_model: Optional[str] | Omit = omit,
        external_config: voice_create_params.ExternalConfig | Omit = omit,
        extractions: Dict[str, voice_create_params.Extractions] | Omit = omit,
        success_criteria: Iterable[voice_create_params.SuccessCriterion] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceDeployment:
        """
        Create a new voice deployment

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return await self._post(
            f"/api/workers/{worker_id}/deployments/voice",
            body=await async_maybe_transform(
                {
                    "flow_id": flow_id,
                    "name": name,
                    "phone_number": phone_number,
                    "backup_phone_message": backup_phone_message,
                    "backup_phone_number": backup_phone_number,
                    "enable_voice_sentiment": enable_voice_sentiment,
                    "engine_model": engine_model,
                    "external_config": external_config,
                    "extractions": extractions,
                    "success_criteria": success_criteria,
                },
                voice_create_params.VoiceCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceDeployment,
        )

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
    ) -> VoiceDeployment:
        """
        Get a single voice deployment

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
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceDeployment,
        )

    async def update(
        self,
        deployment_id: str,
        *,
        worker_id: str,
        backup_phone_message: str | Omit = omit,
        backup_phone_number: str | Omit = omit,
        custom_webhooks: Iterable[voice_update_params.CustomWebhook] | Omit = omit,
        enable_voice_sentiment: bool | Omit = omit,
        engine_model: Optional[str] | Omit = omit,
        external_config: voice_update_params.ExternalConfig | Omit = omit,
        extractions: Dict[str, voice_update_params.Extractions] | Omit = omit,
        flow_id: str | Omit = omit,
        name: str | Omit = omit,
        phone_number: str | Omit = omit,
        success_criteria: Iterable[voice_update_params.SuccessCriterion] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceDeployment:
        """
        Update a voice deployment

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
        return await self._patch(
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}",
            body=await async_maybe_transform(
                {
                    "backup_phone_message": backup_phone_message,
                    "backup_phone_number": backup_phone_number,
                    "custom_webhooks": custom_webhooks,
                    "enable_voice_sentiment": enable_voice_sentiment,
                    "engine_model": engine_model,
                    "external_config": external_config,
                    "extractions": extractions,
                    "flow_id": flow_id,
                    "name": name,
                    "phone_number": phone_number,
                    "success_criteria": success_criteria,
                },
                voice_update_params.VoiceUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceDeployment,
        )

    async def list(
        self,
        worker_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceListResponse:
        """
        Get all voice deployments for a worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return await self._get(
            f"/api/workers/{worker_id}/deployments/voice",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceListResponse,
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
        Delete a voice deployment

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
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def make_batch_calls(
        self,
        deployment_id: str,
        *,
        worker_id: str,
        data: Iterable[Dict[str, str]],
        additional_data: str | Omit = omit,
        batch_interval_minutes: float | Omit = omit,
        batch_size: float | Omit = omit,
        condition: Optional[str] | Omit = omit,
        country: str | Omit = omit,
        extractions: Optional[str] | Omit = omit,
        ws_url: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceMakeBatchCallsResponse:
        """
        Make batch calls for a voice deployment

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
        return await self._post(
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}/make-batch-calls",
            body=await async_maybe_transform(
                {
                    "data": data,
                    "additional_data": additional_data,
                    "batch_interval_minutes": batch_interval_minutes,
                    "batch_size": batch_size,
                    "condition": condition,
                    "country": country,
                    "extractions": extractions,
                    "ws_url": ws_url,
                },
                voice_make_batch_calls_params.VoiceMakeBatchCallsParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceMakeBatchCallsResponse,
        )

    async def stop_batch_calls(
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
    ) -> VoiceStopBatchCallsResponse:
        """
        Removes all scheduled batch calls for the specified deployment from the queue
        and returns the removed items

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
        return await self._post(
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}/stop-batch-calls",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceStopBatchCallsResponse,
        )

    async def stop_campaign(
        self,
        deployment_id: str,
        *,
        worker_id: str,
        campaign_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceStopCampaignResponse:
        """
        Removes all scheduled calls for a specific campaign from the Redis queue

        Args:
          campaign_id: The campaign ID to stop

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
            f"/api/workers/{worker_id}/deployments/voice/{deployment_id}/stop-campaign",
            body=await async_maybe_transform(
                {"campaign_id": campaign_id}, voice_stop_campaign_params.VoiceStopCampaignParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceStopCampaignResponse,
        )


class VoiceResourceWithRawResponse:
    def __init__(self, voice: VoiceResource) -> None:
        self._voice = voice

        self.create = to_raw_response_wrapper(
            voice.create,
        )
        self.retrieve = to_raw_response_wrapper(
            voice.retrieve,
        )
        self.update = to_raw_response_wrapper(
            voice.update,
        )
        self.list = to_raw_response_wrapper(
            voice.list,
        )
        self.delete = to_raw_response_wrapper(
            voice.delete,
        )
        self.make_batch_calls = to_raw_response_wrapper(
            voice.make_batch_calls,
        )
        self.stop_batch_calls = to_raw_response_wrapper(
            voice.stop_batch_calls,
        )
        self.stop_campaign = to_raw_response_wrapper(
            voice.stop_campaign,
        )

    @cached_property
    def custom_webhooks(self) -> CustomWebhooksResourceWithRawResponse:
        return CustomWebhooksResourceWithRawResponse(self._voice.custom_webhooks)

    @cached_property
    def outbound_campaigns(self) -> OutboundCampaignsResourceWithRawResponse:
        return OutboundCampaignsResourceWithRawResponse(self._voice.outbound_campaigns)


class AsyncVoiceResourceWithRawResponse:
    def __init__(self, voice: AsyncVoiceResource) -> None:
        self._voice = voice

        self.create = async_to_raw_response_wrapper(
            voice.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            voice.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            voice.update,
        )
        self.list = async_to_raw_response_wrapper(
            voice.list,
        )
        self.delete = async_to_raw_response_wrapper(
            voice.delete,
        )
        self.make_batch_calls = async_to_raw_response_wrapper(
            voice.make_batch_calls,
        )
        self.stop_batch_calls = async_to_raw_response_wrapper(
            voice.stop_batch_calls,
        )
        self.stop_campaign = async_to_raw_response_wrapper(
            voice.stop_campaign,
        )

    @cached_property
    def custom_webhooks(self) -> AsyncCustomWebhooksResourceWithRawResponse:
        return AsyncCustomWebhooksResourceWithRawResponse(self._voice.custom_webhooks)

    @cached_property
    def outbound_campaigns(self) -> AsyncOutboundCampaignsResourceWithRawResponse:
        return AsyncOutboundCampaignsResourceWithRawResponse(self._voice.outbound_campaigns)


class VoiceResourceWithStreamingResponse:
    def __init__(self, voice: VoiceResource) -> None:
        self._voice = voice

        self.create = to_streamed_response_wrapper(
            voice.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            voice.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            voice.update,
        )
        self.list = to_streamed_response_wrapper(
            voice.list,
        )
        self.delete = to_streamed_response_wrapper(
            voice.delete,
        )
        self.make_batch_calls = to_streamed_response_wrapper(
            voice.make_batch_calls,
        )
        self.stop_batch_calls = to_streamed_response_wrapper(
            voice.stop_batch_calls,
        )
        self.stop_campaign = to_streamed_response_wrapper(
            voice.stop_campaign,
        )

    @cached_property
    def custom_webhooks(self) -> CustomWebhooksResourceWithStreamingResponse:
        return CustomWebhooksResourceWithStreamingResponse(self._voice.custom_webhooks)

    @cached_property
    def outbound_campaigns(self) -> OutboundCampaignsResourceWithStreamingResponse:
        return OutboundCampaignsResourceWithStreamingResponse(self._voice.outbound_campaigns)


class AsyncVoiceResourceWithStreamingResponse:
    def __init__(self, voice: AsyncVoiceResource) -> None:
        self._voice = voice

        self.create = async_to_streamed_response_wrapper(
            voice.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            voice.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            voice.update,
        )
        self.list = async_to_streamed_response_wrapper(
            voice.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            voice.delete,
        )
        self.make_batch_calls = async_to_streamed_response_wrapper(
            voice.make_batch_calls,
        )
        self.stop_batch_calls = async_to_streamed_response_wrapper(
            voice.stop_batch_calls,
        )
        self.stop_campaign = async_to_streamed_response_wrapper(
            voice.stop_campaign,
        )

    @cached_property
    def custom_webhooks(self) -> AsyncCustomWebhooksResourceWithStreamingResponse:
        return AsyncCustomWebhooksResourceWithStreamingResponse(self._voice.custom_webhooks)

    @cached_property
    def outbound_campaigns(self) -> AsyncOutboundCampaignsResourceWithStreamingResponse:
        return AsyncOutboundCampaignsResourceWithStreamingResponse(self._voice.outbound_campaigns)

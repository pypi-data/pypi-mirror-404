# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable, Optional

import httpx

from ....._types import Body, Omit, Query, Headers, NoneType, NotGiven, SequenceNotStr, omit, not_given
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
from .campaigns.campaigns import (
    CampaignsResource,
    AsyncCampaignsResource,
    CampaignsResourceWithRawResponse,
    AsyncCampaignsResourceWithRawResponse,
    CampaignsResourceWithStreamingResponse,
    AsyncCampaignsResourceWithStreamingResponse,
)
from .....types.workers.deployments import voicev1_create_params, voicev1_update_params, voicev1_make_batch_calls_params
from .....types.shared.voice_v1_deployment import VoiceV1Deployment
from .....types.workers.deployments.voicev1_list_response import Voicev1ListResponse

__all__ = ["Voicev1Resource", "AsyncVoicev1Resource"]


class Voicev1Resource(SyncAPIResource):
    @cached_property
    def campaigns(self) -> CampaignsResource:
        return CampaignsResource(self._client)

    @cached_property
    def with_raw_response(self) -> Voicev1ResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return Voicev1ResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> Voicev1ResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return Voicev1ResourceWithStreamingResponse(self)

    def create(
        self,
        worker_id: str,
        *,
        allowed_transfer_numbers: SequenceNotStr[str],
        config: object,
        end_sentence: Optional[str],
        flow_id: str,
        functions: Optional[str],
        language: Optional[str],
        model: Optional[str],
        name: str,
        objective: str,
        phone_number: str,
        resource_keys: SequenceNotStr[str],
        start_sentence: Optional[str],
        voice_id: Optional[str],
        ws_base_url: Optional[str],
        extractions: Dict[str, voicev1_create_params.Extractions] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceV1Deployment:
        """
        Create a new voice v1 deployment

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return self._post(
            f"/api/workers/{worker_id}/deployments/voicev1",
            body=maybe_transform(
                {
                    "allowed_transfer_numbers": allowed_transfer_numbers,
                    "config": config,
                    "end_sentence": end_sentence,
                    "flow_id": flow_id,
                    "functions": functions,
                    "language": language,
                    "model": model,
                    "name": name,
                    "objective": objective,
                    "phone_number": phone_number,
                    "resource_keys": resource_keys,
                    "start_sentence": start_sentence,
                    "voice_id": voice_id,
                    "ws_base_url": ws_base_url,
                    "extractions": extractions,
                },
                voicev1_create_params.Voicev1CreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceV1Deployment,
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
    ) -> VoiceV1Deployment:
        """
        Get a single voice v1 deployment

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
            f"/api/workers/{worker_id}/deployments/voicev1/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceV1Deployment,
        )

    def update(
        self,
        deployment_id: str,
        *,
        worker_id: str,
        allowed_transfer_numbers: SequenceNotStr[str] | Omit = omit,
        config: str | Omit = omit,
        end_sentence: Optional[str] | Omit = omit,
        extractions: Dict[str, voicev1_update_params.Extractions] | Omit = omit,
        flow_id: str | Omit = omit,
        functions: Optional[str] | Omit = omit,
        language: Optional[str] | Omit = omit,
        model: Optional[str] | Omit = omit,
        name: str | Omit = omit,
        objective: str | Omit = omit,
        phone_number: str | Omit = omit,
        resource_keys: SequenceNotStr[str] | Omit = omit,
        start_sentence: Optional[str] | Omit = omit,
        voice_id: Optional[str] | Omit = omit,
        ws_base_url: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceV1Deployment:
        """
        Update a voice v1 deployment

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
        return self._put(
            f"/api/workers/{worker_id}/deployments/voicev1/{deployment_id}",
            body=maybe_transform(
                {
                    "allowed_transfer_numbers": allowed_transfer_numbers,
                    "config": config,
                    "end_sentence": end_sentence,
                    "extractions": extractions,
                    "flow_id": flow_id,
                    "functions": functions,
                    "language": language,
                    "model": model,
                    "name": name,
                    "objective": objective,
                    "phone_number": phone_number,
                    "resource_keys": resource_keys,
                    "start_sentence": start_sentence,
                    "voice_id": voice_id,
                    "ws_base_url": ws_base_url,
                },
                voicev1_update_params.Voicev1UpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceV1Deployment,
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
    ) -> Voicev1ListResponse:
        """
        Get all voice v1 deployments for a worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return self._get(
            f"/api/workers/{worker_id}/deployments/voicev1",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Voicev1ListResponse,
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
        Delete a voice v1 deployment

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
            f"/api/workers/{worker_id}/deployments/voicev1/{deployment_id}",
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
        data: Iterable[voicev1_make_batch_calls_params.Data],
        additional_data: Dict[str, str] | Omit = omit,
        batch_interval_minutes: float | Omit = omit,
        batch_size: float | Omit = omit,
        condition: str | Omit = omit,
        extractions: Dict[str, voicev1_make_batch_calls_params.Extractions] | Omit = omit,
        ws_url: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Make batch calls for a voice v1 deployment

        Args:
          data: Array of data objects to process in batches, each requiring at least an id and
              phoneNumber

          additional_data: Additional data to pass with each request that will be available during the call

          batch_interval_minutes: Time interval between batches in minutes (default 5)

          batch_size: Number of items to process in each batch (default 10)

          condition: Optional condition to evaluate for processing data. Supports template variables
              like {{variableName}}

          extractions: Definitions of data to extract during calls, with each key representing a field
              to extract

          ws_url: Webhook URL to receive events when calls complete or extract data

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
        return self._post(
            f"/api/workers/{worker_id}/deployments/voicev1/{deployment_id}/make-batch-calls",
            body=maybe_transform(
                {
                    "data": data,
                    "additional_data": additional_data,
                    "batch_interval_minutes": batch_interval_minutes,
                    "batch_size": batch_size,
                    "condition": condition,
                    "extractions": extractions,
                    "ws_url": ws_url,
                },
                voicev1_make_batch_calls_params.Voicev1MakeBatchCallsParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncVoicev1Resource(AsyncAPIResource):
    @cached_property
    def campaigns(self) -> AsyncCampaignsResource:
        return AsyncCampaignsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncVoicev1ResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncVoicev1ResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncVoicev1ResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncVoicev1ResourceWithStreamingResponse(self)

    async def create(
        self,
        worker_id: str,
        *,
        allowed_transfer_numbers: SequenceNotStr[str],
        config: object,
        end_sentence: Optional[str],
        flow_id: str,
        functions: Optional[str],
        language: Optional[str],
        model: Optional[str],
        name: str,
        objective: str,
        phone_number: str,
        resource_keys: SequenceNotStr[str],
        start_sentence: Optional[str],
        voice_id: Optional[str],
        ws_base_url: Optional[str],
        extractions: Dict[str, voicev1_create_params.Extractions] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceV1Deployment:
        """
        Create a new voice v1 deployment

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return await self._post(
            f"/api/workers/{worker_id}/deployments/voicev1",
            body=await async_maybe_transform(
                {
                    "allowed_transfer_numbers": allowed_transfer_numbers,
                    "config": config,
                    "end_sentence": end_sentence,
                    "flow_id": flow_id,
                    "functions": functions,
                    "language": language,
                    "model": model,
                    "name": name,
                    "objective": objective,
                    "phone_number": phone_number,
                    "resource_keys": resource_keys,
                    "start_sentence": start_sentence,
                    "voice_id": voice_id,
                    "ws_base_url": ws_base_url,
                    "extractions": extractions,
                },
                voicev1_create_params.Voicev1CreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceV1Deployment,
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
    ) -> VoiceV1Deployment:
        """
        Get a single voice v1 deployment

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
            f"/api/workers/{worker_id}/deployments/voicev1/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceV1Deployment,
        )

    async def update(
        self,
        deployment_id: str,
        *,
        worker_id: str,
        allowed_transfer_numbers: SequenceNotStr[str] | Omit = omit,
        config: str | Omit = omit,
        end_sentence: Optional[str] | Omit = omit,
        extractions: Dict[str, voicev1_update_params.Extractions] | Omit = omit,
        flow_id: str | Omit = omit,
        functions: Optional[str] | Omit = omit,
        language: Optional[str] | Omit = omit,
        model: Optional[str] | Omit = omit,
        name: str | Omit = omit,
        objective: str | Omit = omit,
        phone_number: str | Omit = omit,
        resource_keys: SequenceNotStr[str] | Omit = omit,
        start_sentence: Optional[str] | Omit = omit,
        voice_id: Optional[str] | Omit = omit,
        ws_base_url: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VoiceV1Deployment:
        """
        Update a voice v1 deployment

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
        return await self._put(
            f"/api/workers/{worker_id}/deployments/voicev1/{deployment_id}",
            body=await async_maybe_transform(
                {
                    "allowed_transfer_numbers": allowed_transfer_numbers,
                    "config": config,
                    "end_sentence": end_sentence,
                    "extractions": extractions,
                    "flow_id": flow_id,
                    "functions": functions,
                    "language": language,
                    "model": model,
                    "name": name,
                    "objective": objective,
                    "phone_number": phone_number,
                    "resource_keys": resource_keys,
                    "start_sentence": start_sentence,
                    "voice_id": voice_id,
                    "ws_base_url": ws_base_url,
                },
                voicev1_update_params.Voicev1UpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VoiceV1Deployment,
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
    ) -> Voicev1ListResponse:
        """
        Get all voice v1 deployments for a worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return await self._get(
            f"/api/workers/{worker_id}/deployments/voicev1",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Voicev1ListResponse,
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
        Delete a voice v1 deployment

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
            f"/api/workers/{worker_id}/deployments/voicev1/{deployment_id}",
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
        data: Iterable[voicev1_make_batch_calls_params.Data],
        additional_data: Dict[str, str] | Omit = omit,
        batch_interval_minutes: float | Omit = omit,
        batch_size: float | Omit = omit,
        condition: str | Omit = omit,
        extractions: Dict[str, voicev1_make_batch_calls_params.Extractions] | Omit = omit,
        ws_url: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Make batch calls for a voice v1 deployment

        Args:
          data: Array of data objects to process in batches, each requiring at least an id and
              phoneNumber

          additional_data: Additional data to pass with each request that will be available during the call

          batch_interval_minutes: Time interval between batches in minutes (default 5)

          batch_size: Number of items to process in each batch (default 10)

          condition: Optional condition to evaluate for processing data. Supports template variables
              like {{variableName}}

          extractions: Definitions of data to extract during calls, with each key representing a field
              to extract

          ws_url: Webhook URL to receive events when calls complete or extract data

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
        return await self._post(
            f"/api/workers/{worker_id}/deployments/voicev1/{deployment_id}/make-batch-calls",
            body=await async_maybe_transform(
                {
                    "data": data,
                    "additional_data": additional_data,
                    "batch_interval_minutes": batch_interval_minutes,
                    "batch_size": batch_size,
                    "condition": condition,
                    "extractions": extractions,
                    "ws_url": ws_url,
                },
                voicev1_make_batch_calls_params.Voicev1MakeBatchCallsParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class Voicev1ResourceWithRawResponse:
    def __init__(self, voicev1: Voicev1Resource) -> None:
        self._voicev1 = voicev1

        self.create = to_raw_response_wrapper(
            voicev1.create,
        )
        self.retrieve = to_raw_response_wrapper(
            voicev1.retrieve,
        )
        self.update = to_raw_response_wrapper(
            voicev1.update,
        )
        self.list = to_raw_response_wrapper(
            voicev1.list,
        )
        self.delete = to_raw_response_wrapper(
            voicev1.delete,
        )
        self.make_batch_calls = to_raw_response_wrapper(
            voicev1.make_batch_calls,
        )

    @cached_property
    def campaigns(self) -> CampaignsResourceWithRawResponse:
        return CampaignsResourceWithRawResponse(self._voicev1.campaigns)


class AsyncVoicev1ResourceWithRawResponse:
    def __init__(self, voicev1: AsyncVoicev1Resource) -> None:
        self._voicev1 = voicev1

        self.create = async_to_raw_response_wrapper(
            voicev1.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            voicev1.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            voicev1.update,
        )
        self.list = async_to_raw_response_wrapper(
            voicev1.list,
        )
        self.delete = async_to_raw_response_wrapper(
            voicev1.delete,
        )
        self.make_batch_calls = async_to_raw_response_wrapper(
            voicev1.make_batch_calls,
        )

    @cached_property
    def campaigns(self) -> AsyncCampaignsResourceWithRawResponse:
        return AsyncCampaignsResourceWithRawResponse(self._voicev1.campaigns)


class Voicev1ResourceWithStreamingResponse:
    def __init__(self, voicev1: Voicev1Resource) -> None:
        self._voicev1 = voicev1

        self.create = to_streamed_response_wrapper(
            voicev1.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            voicev1.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            voicev1.update,
        )
        self.list = to_streamed_response_wrapper(
            voicev1.list,
        )
        self.delete = to_streamed_response_wrapper(
            voicev1.delete,
        )
        self.make_batch_calls = to_streamed_response_wrapper(
            voicev1.make_batch_calls,
        )

    @cached_property
    def campaigns(self) -> CampaignsResourceWithStreamingResponse:
        return CampaignsResourceWithStreamingResponse(self._voicev1.campaigns)


class AsyncVoicev1ResourceWithStreamingResponse:
    def __init__(self, voicev1: AsyncVoicev1Resource) -> None:
        self._voicev1 = voicev1

        self.create = async_to_streamed_response_wrapper(
            voicev1.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            voicev1.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            voicev1.update,
        )
        self.list = async_to_streamed_response_wrapper(
            voicev1.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            voicev1.delete,
        )
        self.make_batch_calls = async_to_streamed_response_wrapper(
            voicev1.make_batch_calls,
        )

    @cached_property
    def campaigns(self) -> AsyncCampaignsResourceWithStreamingResponse:
        return AsyncCampaignsResourceWithStreamingResponse(self._voicev1.campaigns)

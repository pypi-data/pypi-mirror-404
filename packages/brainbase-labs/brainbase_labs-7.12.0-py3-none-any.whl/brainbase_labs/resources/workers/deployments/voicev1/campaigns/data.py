# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ......_types import Body, Omit, Query, Headers, NoneType, NotGiven, omit, not_given
from ......_utils import maybe_transform, async_maybe_transform
from ......_compat import cached_property
from ......_resource import SyncAPIResource, AsyncAPIResource
from ......_response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ......_base_client import make_request_options
from ......types.workers.deployments.voicev1.campaigns import data_update_params

__all__ = ["DataResource", "AsyncDataResource"]


class DataResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> DataResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return DataResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DataResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return DataResourceWithStreamingResponse(self)

    def retrieve(
        self,
        data_id: str,
        *,
        worker_id: str,
        deployment_id: str,
        campaign_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Get specific campaign data by ID

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
        if not data_id:
            raise ValueError(f"Expected a non-empty value for `data_id` but received {data_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._get(
            f"/api/workers/{worker_id}/deployments/voicev1/{deployment_id}/campaigns/{campaign_id}/data/{data_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def update(
        self,
        data_id: str,
        *,
        worker_id: str,
        deployment_id: str,
        campaign_id: str,
        result: object | Omit = omit,
        row_data: object | Omit = omit,
        status: Literal["PENDING", "PROCESSING", "COMPLETED", "FAILED"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Update specific campaign data by ID

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
        if not data_id:
            raise ValueError(f"Expected a non-empty value for `data_id` but received {data_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._put(
            f"/api/workers/{worker_id}/deployments/voicev1/{deployment_id}/campaigns/{campaign_id}/data/{data_id}",
            body=maybe_transform(
                {
                    "result": result,
                    "row_data": row_data,
                    "status": status,
                },
                data_update_params.DataUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncDataResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncDataResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncDataResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDataResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncDataResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        data_id: str,
        *,
        worker_id: str,
        deployment_id: str,
        campaign_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Get specific campaign data by ID

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
        if not data_id:
            raise ValueError(f"Expected a non-empty value for `data_id` but received {data_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._get(
            f"/api/workers/{worker_id}/deployments/voicev1/{deployment_id}/campaigns/{campaign_id}/data/{data_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def update(
        self,
        data_id: str,
        *,
        worker_id: str,
        deployment_id: str,
        campaign_id: str,
        result: object | Omit = omit,
        row_data: object | Omit = omit,
        status: Literal["PENDING", "PROCESSING", "COMPLETED", "FAILED"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Update specific campaign data by ID

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
        if not data_id:
            raise ValueError(f"Expected a non-empty value for `data_id` but received {data_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._put(
            f"/api/workers/{worker_id}/deployments/voicev1/{deployment_id}/campaigns/{campaign_id}/data/{data_id}",
            body=await async_maybe_transform(
                {
                    "result": result,
                    "row_data": row_data,
                    "status": status,
                },
                data_update_params.DataUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class DataResourceWithRawResponse:
    def __init__(self, data: DataResource) -> None:
        self._data = data

        self.retrieve = to_raw_response_wrapper(
            data.retrieve,
        )
        self.update = to_raw_response_wrapper(
            data.update,
        )


class AsyncDataResourceWithRawResponse:
    def __init__(self, data: AsyncDataResource) -> None:
        self._data = data

        self.retrieve = async_to_raw_response_wrapper(
            data.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            data.update,
        )


class DataResourceWithStreamingResponse:
    def __init__(self, data: DataResource) -> None:
        self._data = data

        self.retrieve = to_streamed_response_wrapper(
            data.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            data.update,
        )


class AsyncDataResourceWithStreamingResponse:
    def __init__(self, data: AsyncDataResource) -> None:
        self._data = data

        self.retrieve = async_to_streamed_response_wrapper(
            data.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            data.update,
        )

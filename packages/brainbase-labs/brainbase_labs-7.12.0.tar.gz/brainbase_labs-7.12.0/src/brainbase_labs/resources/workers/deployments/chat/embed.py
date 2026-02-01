# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict

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
from .....types.workers.deployments.chat import embed_create_params, embed_update_params
from .....types.workers.deployments.chat.embed_list_response import EmbedListResponse
from .....types.workers.deployments.chat.embed_create_response import EmbedCreateResponse
from .....types.workers.deployments.chat.embed_update_response import EmbedUpdateResponse
from .....types.workers.deployments.chat.embed_retrieve_response import EmbedRetrieveResponse
from .....types.workers.deployments.chat.embed_retrieve_by_embed_response import EmbedRetrieveByEmbedResponse

__all__ = ["EmbedResource", "AsyncEmbedResource"]


class EmbedResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> EmbedResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return EmbedResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> EmbedResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return EmbedResourceWithStreamingResponse(self)

    def create(
        self,
        worker_id: str,
        *,
        flow_id: str,
        name: str,
        agent_logo_url: str | Omit = omit,
        agent_name: str | Omit = omit,
        primary_color: str | Omit = omit,
        styling: Dict[str, str] | Omit = omit,
        welcome_message: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmbedCreateResponse:
        """
        Create a new chat embed deployment

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return self._post(
            f"/api/workers/{worker_id}/deployments/chat-embed",
            body=maybe_transform(
                {
                    "flow_id": flow_id,
                    "name": name,
                    "agent_logo_url": agent_logo_url,
                    "agent_name": agent_name,
                    "primary_color": primary_color,
                    "styling": styling,
                    "welcome_message": welcome_message,
                },
                embed_create_params.EmbedCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmbedCreateResponse,
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
    ) -> EmbedRetrieveResponse:
        """
        Get a single chat embed deployment by ID

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
            f"/api/workers/{worker_id}/deployments/chat-embed/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmbedRetrieveResponse,
        )

    def update(
        self,
        deployment_id: str,
        *,
        worker_id: str,
        agent_logo_url: str | Omit = omit,
        agent_name: str | Omit = omit,
        flow_id: str | Omit = omit,
        name: str | Omit = omit,
        primary_color: str | Omit = omit,
        styling: Dict[str, str] | Omit = omit,
        welcome_message: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmbedUpdateResponse:
        """
        Update a chat embed deployment

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
            f"/api/workers/{worker_id}/deployments/chat-embed/{deployment_id}",
            body=maybe_transform(
                {
                    "agent_logo_url": agent_logo_url,
                    "agent_name": agent_name,
                    "flow_id": flow_id,
                    "name": name,
                    "primary_color": primary_color,
                    "styling": styling,
                    "welcome_message": welcome_message,
                },
                embed_update_params.EmbedUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmbedUpdateResponse,
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
    ) -> EmbedListResponse:
        """
        Get all chat embed deployments for a worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return self._get(
            f"/api/workers/{worker_id}/deployments/chat-embed",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmbedListResponse,
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
        Delete a chat embed deployment

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
            f"/api/workers/{worker_id}/deployments/chat-embed/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def retrieve_by_embed(
        self,
        embed_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmbedRetrieveByEmbedResponse:
        """
        Get a single chat embed deployment by embed ID

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not embed_id:
            raise ValueError(f"Expected a non-empty value for `embed_id` but received {embed_id!r}")
        return self._get(
            f"/api/workers/deployments/chat-embed/by-embed/{embed_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmbedRetrieveByEmbedResponse,
        )


class AsyncEmbedResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncEmbedResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncEmbedResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncEmbedResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncEmbedResourceWithStreamingResponse(self)

    async def create(
        self,
        worker_id: str,
        *,
        flow_id: str,
        name: str,
        agent_logo_url: str | Omit = omit,
        agent_name: str | Omit = omit,
        primary_color: str | Omit = omit,
        styling: Dict[str, str] | Omit = omit,
        welcome_message: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmbedCreateResponse:
        """
        Create a new chat embed deployment

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return await self._post(
            f"/api/workers/{worker_id}/deployments/chat-embed",
            body=await async_maybe_transform(
                {
                    "flow_id": flow_id,
                    "name": name,
                    "agent_logo_url": agent_logo_url,
                    "agent_name": agent_name,
                    "primary_color": primary_color,
                    "styling": styling,
                    "welcome_message": welcome_message,
                },
                embed_create_params.EmbedCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmbedCreateResponse,
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
    ) -> EmbedRetrieveResponse:
        """
        Get a single chat embed deployment by ID

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
            f"/api/workers/{worker_id}/deployments/chat-embed/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmbedRetrieveResponse,
        )

    async def update(
        self,
        deployment_id: str,
        *,
        worker_id: str,
        agent_logo_url: str | Omit = omit,
        agent_name: str | Omit = omit,
        flow_id: str | Omit = omit,
        name: str | Omit = omit,
        primary_color: str | Omit = omit,
        styling: Dict[str, str] | Omit = omit,
        welcome_message: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmbedUpdateResponse:
        """
        Update a chat embed deployment

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
            f"/api/workers/{worker_id}/deployments/chat-embed/{deployment_id}",
            body=await async_maybe_transform(
                {
                    "agent_logo_url": agent_logo_url,
                    "agent_name": agent_name,
                    "flow_id": flow_id,
                    "name": name,
                    "primary_color": primary_color,
                    "styling": styling,
                    "welcome_message": welcome_message,
                },
                embed_update_params.EmbedUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmbedUpdateResponse,
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
    ) -> EmbedListResponse:
        """
        Get all chat embed deployments for a worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return await self._get(
            f"/api/workers/{worker_id}/deployments/chat-embed",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmbedListResponse,
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
        Delete a chat embed deployment

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
            f"/api/workers/{worker_id}/deployments/chat-embed/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def retrieve_by_embed(
        self,
        embed_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmbedRetrieveByEmbedResponse:
        """
        Get a single chat embed deployment by embed ID

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not embed_id:
            raise ValueError(f"Expected a non-empty value for `embed_id` but received {embed_id!r}")
        return await self._get(
            f"/api/workers/deployments/chat-embed/by-embed/{embed_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmbedRetrieveByEmbedResponse,
        )


class EmbedResourceWithRawResponse:
    def __init__(self, embed: EmbedResource) -> None:
        self._embed = embed

        self.create = to_raw_response_wrapper(
            embed.create,
        )
        self.retrieve = to_raw_response_wrapper(
            embed.retrieve,
        )
        self.update = to_raw_response_wrapper(
            embed.update,
        )
        self.list = to_raw_response_wrapper(
            embed.list,
        )
        self.delete = to_raw_response_wrapper(
            embed.delete,
        )
        self.retrieve_by_embed = to_raw_response_wrapper(
            embed.retrieve_by_embed,
        )


class AsyncEmbedResourceWithRawResponse:
    def __init__(self, embed: AsyncEmbedResource) -> None:
        self._embed = embed

        self.create = async_to_raw_response_wrapper(
            embed.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            embed.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            embed.update,
        )
        self.list = async_to_raw_response_wrapper(
            embed.list,
        )
        self.delete = async_to_raw_response_wrapper(
            embed.delete,
        )
        self.retrieve_by_embed = async_to_raw_response_wrapper(
            embed.retrieve_by_embed,
        )


class EmbedResourceWithStreamingResponse:
    def __init__(self, embed: EmbedResource) -> None:
        self._embed = embed

        self.create = to_streamed_response_wrapper(
            embed.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            embed.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            embed.update,
        )
        self.list = to_streamed_response_wrapper(
            embed.list,
        )
        self.delete = to_streamed_response_wrapper(
            embed.delete,
        )
        self.retrieve_by_embed = to_streamed_response_wrapper(
            embed.retrieve_by_embed,
        )


class AsyncEmbedResourceWithStreamingResponse:
    def __init__(self, embed: AsyncEmbedResource) -> None:
        self._embed = embed

        self.create = async_to_streamed_response_wrapper(
            embed.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            embed.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            embed.update,
        )
        self.list = async_to_streamed_response_wrapper(
            embed.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            embed.delete,
        )
        self.retrieve_by_embed = async_to_streamed_response_wrapper(
            embed.retrieve_by_embed,
        )

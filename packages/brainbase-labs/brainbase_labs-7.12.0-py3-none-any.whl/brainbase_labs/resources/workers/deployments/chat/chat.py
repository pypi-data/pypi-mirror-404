# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable

import httpx

from .embed import (
    EmbedResource,
    AsyncEmbedResource,
    EmbedResourceWithRawResponse,
    AsyncEmbedResourceWithRawResponse,
    EmbedResourceWithStreamingResponse,
    AsyncEmbedResourceWithStreamingResponse,
)
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
from .....types.workers.deployments import chat_create_params, chat_update_params
from .....types.workers.deployments.chat_list_response import ChatListResponse
from .....types.workers.deployments.chat_create_response import ChatCreateResponse
from .....types.workers.deployments.chat_update_response import ChatUpdateResponse
from .....types.workers.deployments.chat_retrieve_response import ChatRetrieveResponse
from .....types.workers.deployments.chat_retrieve_agent_response import ChatRetrieveAgentResponse

__all__ = ["ChatResource", "AsyncChatResource"]


class ChatResource(SyncAPIResource):
    @cached_property
    def embed(self) -> EmbedResource:
        return EmbedResource(self._client)

    @cached_property
    def with_raw_response(self) -> ChatResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return ChatResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ChatResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return ChatResourceWithStreamingResponse(self)

    def create(
        self,
        worker_id: str,
        *,
        flow_id: str,
        name: str,
        allowed_users: SequenceNotStr[str] | Omit = omit,
        extractions: Dict[str, chat_create_params.Extractions] | Omit = omit,
        llm_model: str | Omit = omit,
        model_config: Dict[str, str] | Omit = omit,
        success_criteria: Iterable[chat_create_params.SuccessCriterion] | Omit = omit,
        welcome_message: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChatCreateResponse:
        """
        Create a new chat deployment

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return self._post(
            f"/api/workers/{worker_id}/deployments/chat",
            body=maybe_transform(
                {
                    "flow_id": flow_id,
                    "name": name,
                    "allowed_users": allowed_users,
                    "extractions": extractions,
                    "llm_model": llm_model,
                    "model_config": model_config,
                    "success_criteria": success_criteria,
                    "welcome_message": welcome_message,
                },
                chat_create_params.ChatCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChatCreateResponse,
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
    ) -> ChatRetrieveResponse:
        """
        Get a single chat deployment by ID

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
            f"/api/workers/{worker_id}/deployments/chat/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChatRetrieveResponse,
        )

    def update(
        self,
        deployment_id: str,
        *,
        worker_id: str,
        allowed_users: SequenceNotStr[str] | Omit = omit,
        extractions: Dict[str, chat_update_params.Extractions] | Omit = omit,
        flow_id: str | Omit = omit,
        llm_model: str | Omit = omit,
        model_config: Dict[str, str] | Omit = omit,
        name: str | Omit = omit,
        success_criteria: Iterable[chat_update_params.SuccessCriterion] | Omit = omit,
        welcome_message: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChatUpdateResponse:
        """
        Update a chat deployment

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
            f"/api/workers/{worker_id}/deployments/chat/{deployment_id}",
            body=maybe_transform(
                {
                    "allowed_users": allowed_users,
                    "extractions": extractions,
                    "flow_id": flow_id,
                    "llm_model": llm_model,
                    "model_config": model_config,
                    "name": name,
                    "success_criteria": success_criteria,
                    "welcome_message": welcome_message,
                },
                chat_update_params.ChatUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChatUpdateResponse,
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
    ) -> ChatListResponse:
        """
        Get all chat deployments for a worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return self._get(
            f"/api/workers/{worker_id}/deployments/chat",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChatListResponse,
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
        Delete a chat deployment

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
            f"/api/workers/{worker_id}/deployments/chat/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def retrieve_agent(
        self,
        chat_agent_id: str,
        *,
        worker_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChatRetrieveAgentResponse:
        """
        Get a single chat deployment by chat agent ID

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not chat_agent_id:
            raise ValueError(f"Expected a non-empty value for `chat_agent_id` but received {chat_agent_id!r}")
        return self._get(
            f"/api/workers/{worker_id}/deployments/chat/agent/{chat_agent_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChatRetrieveAgentResponse,
        )


class AsyncChatResource(AsyncAPIResource):
    @cached_property
    def embed(self) -> AsyncEmbedResource:
        return AsyncEmbedResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncChatResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncChatResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncChatResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncChatResourceWithStreamingResponse(self)

    async def create(
        self,
        worker_id: str,
        *,
        flow_id: str,
        name: str,
        allowed_users: SequenceNotStr[str] | Omit = omit,
        extractions: Dict[str, chat_create_params.Extractions] | Omit = omit,
        llm_model: str | Omit = omit,
        model_config: Dict[str, str] | Omit = omit,
        success_criteria: Iterable[chat_create_params.SuccessCriterion] | Omit = omit,
        welcome_message: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChatCreateResponse:
        """
        Create a new chat deployment

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return await self._post(
            f"/api/workers/{worker_id}/deployments/chat",
            body=await async_maybe_transform(
                {
                    "flow_id": flow_id,
                    "name": name,
                    "allowed_users": allowed_users,
                    "extractions": extractions,
                    "llm_model": llm_model,
                    "model_config": model_config,
                    "success_criteria": success_criteria,
                    "welcome_message": welcome_message,
                },
                chat_create_params.ChatCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChatCreateResponse,
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
    ) -> ChatRetrieveResponse:
        """
        Get a single chat deployment by ID

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
            f"/api/workers/{worker_id}/deployments/chat/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChatRetrieveResponse,
        )

    async def update(
        self,
        deployment_id: str,
        *,
        worker_id: str,
        allowed_users: SequenceNotStr[str] | Omit = omit,
        extractions: Dict[str, chat_update_params.Extractions] | Omit = omit,
        flow_id: str | Omit = omit,
        llm_model: str | Omit = omit,
        model_config: Dict[str, str] | Omit = omit,
        name: str | Omit = omit,
        success_criteria: Iterable[chat_update_params.SuccessCriterion] | Omit = omit,
        welcome_message: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChatUpdateResponse:
        """
        Update a chat deployment

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
            f"/api/workers/{worker_id}/deployments/chat/{deployment_id}",
            body=await async_maybe_transform(
                {
                    "allowed_users": allowed_users,
                    "extractions": extractions,
                    "flow_id": flow_id,
                    "llm_model": llm_model,
                    "model_config": model_config,
                    "name": name,
                    "success_criteria": success_criteria,
                    "welcome_message": welcome_message,
                },
                chat_update_params.ChatUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChatUpdateResponse,
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
    ) -> ChatListResponse:
        """
        Get all chat deployments for a worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        return await self._get(
            f"/api/workers/{worker_id}/deployments/chat",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChatListResponse,
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
        Delete a chat deployment

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
            f"/api/workers/{worker_id}/deployments/chat/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def retrieve_agent(
        self,
        chat_agent_id: str,
        *,
        worker_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChatRetrieveAgentResponse:
        """
        Get a single chat deployment by chat agent ID

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not chat_agent_id:
            raise ValueError(f"Expected a non-empty value for `chat_agent_id` but received {chat_agent_id!r}")
        return await self._get(
            f"/api/workers/{worker_id}/deployments/chat/agent/{chat_agent_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChatRetrieveAgentResponse,
        )


class ChatResourceWithRawResponse:
    def __init__(self, chat: ChatResource) -> None:
        self._chat = chat

        self.create = to_raw_response_wrapper(
            chat.create,
        )
        self.retrieve = to_raw_response_wrapper(
            chat.retrieve,
        )
        self.update = to_raw_response_wrapper(
            chat.update,
        )
        self.list = to_raw_response_wrapper(
            chat.list,
        )
        self.delete = to_raw_response_wrapper(
            chat.delete,
        )
        self.retrieve_agent = to_raw_response_wrapper(
            chat.retrieve_agent,
        )

    @cached_property
    def embed(self) -> EmbedResourceWithRawResponse:
        return EmbedResourceWithRawResponse(self._chat.embed)


class AsyncChatResourceWithRawResponse:
    def __init__(self, chat: AsyncChatResource) -> None:
        self._chat = chat

        self.create = async_to_raw_response_wrapper(
            chat.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            chat.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            chat.update,
        )
        self.list = async_to_raw_response_wrapper(
            chat.list,
        )
        self.delete = async_to_raw_response_wrapper(
            chat.delete,
        )
        self.retrieve_agent = async_to_raw_response_wrapper(
            chat.retrieve_agent,
        )

    @cached_property
    def embed(self) -> AsyncEmbedResourceWithRawResponse:
        return AsyncEmbedResourceWithRawResponse(self._chat.embed)


class ChatResourceWithStreamingResponse:
    def __init__(self, chat: ChatResource) -> None:
        self._chat = chat

        self.create = to_streamed_response_wrapper(
            chat.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            chat.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            chat.update,
        )
        self.list = to_streamed_response_wrapper(
            chat.list,
        )
        self.delete = to_streamed_response_wrapper(
            chat.delete,
        )
        self.retrieve_agent = to_streamed_response_wrapper(
            chat.retrieve_agent,
        )

    @cached_property
    def embed(self) -> EmbedResourceWithStreamingResponse:
        return EmbedResourceWithStreamingResponse(self._chat.embed)


class AsyncChatResourceWithStreamingResponse:
    def __init__(self, chat: AsyncChatResource) -> None:
        self._chat = chat

        self.create = async_to_streamed_response_wrapper(
            chat.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            chat.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            chat.update,
        )
        self.list = async_to_streamed_response_wrapper(
            chat.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            chat.delete,
        )
        self.retrieve_agent = async_to_streamed_response_wrapper(
            chat.retrieve_agent,
        )

    @cached_property
    def embed(self) -> AsyncEmbedResourceWithStreamingResponse:
        return AsyncEmbedResourceWithStreamingResponse(self._chat.embed)

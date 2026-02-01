# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from .flows import (
    FlowsResource,
    AsyncFlowsResource,
    FlowsResourceWithRawResponse,
    AsyncFlowsResourceWithRawResponse,
    FlowsResourceWithStreamingResponse,
    AsyncFlowsResourceWithStreamingResponse,
)
from .tests import (
    TestsResource,
    AsyncTestsResource,
    TestsResourceWithRawResponse,
    AsyncTestsResourceWithRawResponse,
    TestsResourceWithStreamingResponse,
    AsyncTestsResourceWithStreamingResponse,
)
from ...types import worker_create_params, worker_update_params, worker_check_callable_params
from .folders import (
    FoldersResource,
    AsyncFoldersResource,
    FoldersResourceWithRawResponse,
    AsyncFoldersResourceWithRawResponse,
    FoldersResourceWithStreamingResponse,
    AsyncFoldersResourceWithStreamingResponse,
)
from ..._types import Body, Omit, Query, Headers, NoneType, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from .sessions import (
    SessionsResource,
    AsyncSessionsResource,
    SessionsResourceWithRawResponse,
    AsyncSessionsResourceWithRawResponse,
    SessionsResourceWithStreamingResponse,
    AsyncSessionsResourceWithStreamingResponse,
)
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from .business_hours import (
    BusinessHoursResource,
    AsyncBusinessHoursResource,
    BusinessHoursResourceWithRawResponse,
    AsyncBusinessHoursResourceWithRawResponse,
    BusinessHoursResourceWithStreamingResponse,
    AsyncBusinessHoursResourceWithStreamingResponse,
)
from .runtime_errors import (
    RuntimeErrorsResource,
    AsyncRuntimeErrorsResource,
    RuntimeErrorsResourceWithRawResponse,
    AsyncRuntimeErrorsResourceWithRawResponse,
    RuntimeErrorsResourceWithStreamingResponse,
    AsyncRuntimeErrorsResourceWithStreamingResponse,
)
from .team_phone_hours import (
    TeamPhoneHoursResource,
    AsyncTeamPhoneHoursResource,
    TeamPhoneHoursResourceWithRawResponse,
    AsyncTeamPhoneHoursResourceWithRawResponse,
    TeamPhoneHoursResourceWithStreamingResponse,
    AsyncTeamPhoneHoursResourceWithStreamingResponse,
)
from .llm_logs.llm_logs import (
    LlmLogsResource,
    AsyncLlmLogsResource,
    LlmLogsResourceWithRawResponse,
    AsyncLlmLogsResourceWithRawResponse,
    LlmLogsResourceWithStreamingResponse,
    AsyncLlmLogsResourceWithStreamingResponse,
)
from .resources.resources import (
    ResourcesResource,
    AsyncResourcesResource,
    ResourcesResourceWithRawResponse,
    AsyncResourcesResourceWithRawResponse,
    ResourcesResourceWithStreamingResponse,
    AsyncResourcesResourceWithStreamingResponse,
)
from ...types.shared.worker import Worker
from .deployments.deployments import (
    DeploymentsResource,
    AsyncDeploymentsResource,
    DeploymentsResourceWithRawResponse,
    AsyncDeploymentsResourceWithRawResponse,
    DeploymentsResourceWithStreamingResponse,
    AsyncDeploymentsResourceWithStreamingResponse,
)
from ...types.worker_list_response import WorkerListResponse
from .deployment_logs.deployment_logs import (
    DeploymentLogsResource,
    AsyncDeploymentLogsResource,
    DeploymentLogsResourceWithRawResponse,
    AsyncDeploymentLogsResourceWithRawResponse,
    DeploymentLogsResourceWithStreamingResponse,
    AsyncDeploymentLogsResourceWithStreamingResponse,
)
from ...types.worker_check_callable_response import WorkerCheckCallableResponse
from ...types.worker_retrieve_session_response import WorkerRetrieveSessionResponse

__all__ = ["WorkersResource", "AsyncWorkersResource"]


class WorkersResource(SyncAPIResource):
    @cached_property
    def deployments(self) -> DeploymentsResource:
        return DeploymentsResource(self._client)

    @cached_property
    def flows(self) -> FlowsResource:
        return FlowsResource(self._client)

    @cached_property
    def resources(self) -> ResourcesResource:
        return ResourcesResource(self._client)

    @cached_property
    def tests(self) -> TestsResource:
        return TestsResource(self._client)

    @cached_property
    def deployment_logs(self) -> DeploymentLogsResource:
        return DeploymentLogsResource(self._client)

    @cached_property
    def folders(self) -> FoldersResource:
        return FoldersResource(self._client)

    @cached_property
    def business_hours(self) -> BusinessHoursResource:
        return BusinessHoursResource(self._client)

    @cached_property
    def team_phone_hours(self) -> TeamPhoneHoursResource:
        return TeamPhoneHoursResource(self._client)

    @cached_property
    def llm_logs(self) -> LlmLogsResource:
        return LlmLogsResource(self._client)

    @cached_property
    def sessions(self) -> SessionsResource:
        return SessionsResource(self._client)

    @cached_property
    def runtime_errors(self) -> RuntimeErrorsResource:
        return RuntimeErrorsResource(self._client)

    @cached_property
    def with_raw_response(self) -> WorkersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return WorkersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> WorkersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return WorkersResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        description: Optional[str],
        name: str,
        status: Optional[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Worker:
        """
        Create a new worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/workers",
            body=maybe_transform(
                {
                    "description": description,
                    "name": name,
                    "status": status,
                },
                worker_create_params.WorkerCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Worker,
        )

    def retrieve(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Worker:
        """
        Get a single worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/api/workers/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Worker,
        )

    def update(
        self,
        id: str,
        *,
        description: Optional[str] | Omit = omit,
        name: str | Omit = omit,
        status: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Worker:
        """
        Update a worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._patch(
            f"/api/workers/{id}",
            body=maybe_transform(
                {
                    "description": description,
                    "name": name,
                    "status": status,
                },
                worker_update_params.WorkerUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Worker,
        )

    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkerListResponse:
        """Get all workers for the team"""
        return self._get(
            "/api/workers",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkerListResponse,
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
        Delete a worker

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
            f"/api/workers/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def check_callable(
        self,
        *,
        phone_number: str,
        timestamp: float,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkerCheckCallableResponse:
        """Checks if a phone number is callable at a specific timestamp by:

        1.

        Taking a UTC Unix timestamp
        2. Converting it to the business hours timezone (from BusinessHours table)
        3. Checking if the local time falls within the business hours for that day

        Args:
          phone_number: The phone number to check (accepts any format - will be normalized)

          timestamp: Unix timestamp in seconds (UTC). Will be converted to the business hours
              timezone.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/workers/check-callable",
            body=maybe_transform(
                {
                    "phone_number": phone_number,
                    "timestamp": timestamp,
                },
                worker_check_callable_params.WorkerCheckCallableParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkerCheckCallableResponse,
        )

    def retrieve_session(
        self,
        session_id: str,
        *,
        worker_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkerRetrieveSessionResponse:
        """
        Get session data for a specific session

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._get(
            f"/api/workers/{worker_id}/sessions/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkerRetrieveSessionResponse,
        )


class AsyncWorkersResource(AsyncAPIResource):
    @cached_property
    def deployments(self) -> AsyncDeploymentsResource:
        return AsyncDeploymentsResource(self._client)

    @cached_property
    def flows(self) -> AsyncFlowsResource:
        return AsyncFlowsResource(self._client)

    @cached_property
    def resources(self) -> AsyncResourcesResource:
        return AsyncResourcesResource(self._client)

    @cached_property
    def tests(self) -> AsyncTestsResource:
        return AsyncTestsResource(self._client)

    @cached_property
    def deployment_logs(self) -> AsyncDeploymentLogsResource:
        return AsyncDeploymentLogsResource(self._client)

    @cached_property
    def folders(self) -> AsyncFoldersResource:
        return AsyncFoldersResource(self._client)

    @cached_property
    def business_hours(self) -> AsyncBusinessHoursResource:
        return AsyncBusinessHoursResource(self._client)

    @cached_property
    def team_phone_hours(self) -> AsyncTeamPhoneHoursResource:
        return AsyncTeamPhoneHoursResource(self._client)

    @cached_property
    def llm_logs(self) -> AsyncLlmLogsResource:
        return AsyncLlmLogsResource(self._client)

    @cached_property
    def sessions(self) -> AsyncSessionsResource:
        return AsyncSessionsResource(self._client)

    @cached_property
    def runtime_errors(self) -> AsyncRuntimeErrorsResource:
        return AsyncRuntimeErrorsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncWorkersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncWorkersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncWorkersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncWorkersResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        description: Optional[str],
        name: str,
        status: Optional[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Worker:
        """
        Create a new worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/workers",
            body=await async_maybe_transform(
                {
                    "description": description,
                    "name": name,
                    "status": status,
                },
                worker_create_params.WorkerCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Worker,
        )

    async def retrieve(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Worker:
        """
        Get a single worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/api/workers/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Worker,
        )

    async def update(
        self,
        id: str,
        *,
        description: Optional[str] | Omit = omit,
        name: str | Omit = omit,
        status: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Worker:
        """
        Update a worker

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._patch(
            f"/api/workers/{id}",
            body=await async_maybe_transform(
                {
                    "description": description,
                    "name": name,
                    "status": status,
                },
                worker_update_params.WorkerUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Worker,
        )

    async def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkerListResponse:
        """Get all workers for the team"""
        return await self._get(
            "/api/workers",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkerListResponse,
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
        Delete a worker

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
            f"/api/workers/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def check_callable(
        self,
        *,
        phone_number: str,
        timestamp: float,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkerCheckCallableResponse:
        """Checks if a phone number is callable at a specific timestamp by:

        1.

        Taking a UTC Unix timestamp
        2. Converting it to the business hours timezone (from BusinessHours table)
        3. Checking if the local time falls within the business hours for that day

        Args:
          phone_number: The phone number to check (accepts any format - will be normalized)

          timestamp: Unix timestamp in seconds (UTC). Will be converted to the business hours
              timezone.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/workers/check-callable",
            body=await async_maybe_transform(
                {
                    "phone_number": phone_number,
                    "timestamp": timestamp,
                },
                worker_check_callable_params.WorkerCheckCallableParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkerCheckCallableResponse,
        )

    async def retrieve_session(
        self,
        session_id: str,
        *,
        worker_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkerRetrieveSessionResponse:
        """
        Get session data for a specific session

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not worker_id:
            raise ValueError(f"Expected a non-empty value for `worker_id` but received {worker_id!r}")
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._get(
            f"/api/workers/{worker_id}/sessions/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkerRetrieveSessionResponse,
        )


class WorkersResourceWithRawResponse:
    def __init__(self, workers: WorkersResource) -> None:
        self._workers = workers

        self.create = to_raw_response_wrapper(
            workers.create,
        )
        self.retrieve = to_raw_response_wrapper(
            workers.retrieve,
        )
        self.update = to_raw_response_wrapper(
            workers.update,
        )
        self.list = to_raw_response_wrapper(
            workers.list,
        )
        self.delete = to_raw_response_wrapper(
            workers.delete,
        )
        self.check_callable = to_raw_response_wrapper(
            workers.check_callable,
        )
        self.retrieve_session = to_raw_response_wrapper(
            workers.retrieve_session,
        )

    @cached_property
    def deployments(self) -> DeploymentsResourceWithRawResponse:
        return DeploymentsResourceWithRawResponse(self._workers.deployments)

    @cached_property
    def flows(self) -> FlowsResourceWithRawResponse:
        return FlowsResourceWithRawResponse(self._workers.flows)

    @cached_property
    def resources(self) -> ResourcesResourceWithRawResponse:
        return ResourcesResourceWithRawResponse(self._workers.resources)

    @cached_property
    def tests(self) -> TestsResourceWithRawResponse:
        return TestsResourceWithRawResponse(self._workers.tests)

    @cached_property
    def deployment_logs(self) -> DeploymentLogsResourceWithRawResponse:
        return DeploymentLogsResourceWithRawResponse(self._workers.deployment_logs)

    @cached_property
    def folders(self) -> FoldersResourceWithRawResponse:
        return FoldersResourceWithRawResponse(self._workers.folders)

    @cached_property
    def business_hours(self) -> BusinessHoursResourceWithRawResponse:
        return BusinessHoursResourceWithRawResponse(self._workers.business_hours)

    @cached_property
    def team_phone_hours(self) -> TeamPhoneHoursResourceWithRawResponse:
        return TeamPhoneHoursResourceWithRawResponse(self._workers.team_phone_hours)

    @cached_property
    def llm_logs(self) -> LlmLogsResourceWithRawResponse:
        return LlmLogsResourceWithRawResponse(self._workers.llm_logs)

    @cached_property
    def sessions(self) -> SessionsResourceWithRawResponse:
        return SessionsResourceWithRawResponse(self._workers.sessions)

    @cached_property
    def runtime_errors(self) -> RuntimeErrorsResourceWithRawResponse:
        return RuntimeErrorsResourceWithRawResponse(self._workers.runtime_errors)


class AsyncWorkersResourceWithRawResponse:
    def __init__(self, workers: AsyncWorkersResource) -> None:
        self._workers = workers

        self.create = async_to_raw_response_wrapper(
            workers.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            workers.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            workers.update,
        )
        self.list = async_to_raw_response_wrapper(
            workers.list,
        )
        self.delete = async_to_raw_response_wrapper(
            workers.delete,
        )
        self.check_callable = async_to_raw_response_wrapper(
            workers.check_callable,
        )
        self.retrieve_session = async_to_raw_response_wrapper(
            workers.retrieve_session,
        )

    @cached_property
    def deployments(self) -> AsyncDeploymentsResourceWithRawResponse:
        return AsyncDeploymentsResourceWithRawResponse(self._workers.deployments)

    @cached_property
    def flows(self) -> AsyncFlowsResourceWithRawResponse:
        return AsyncFlowsResourceWithRawResponse(self._workers.flows)

    @cached_property
    def resources(self) -> AsyncResourcesResourceWithRawResponse:
        return AsyncResourcesResourceWithRawResponse(self._workers.resources)

    @cached_property
    def tests(self) -> AsyncTestsResourceWithRawResponse:
        return AsyncTestsResourceWithRawResponse(self._workers.tests)

    @cached_property
    def deployment_logs(self) -> AsyncDeploymentLogsResourceWithRawResponse:
        return AsyncDeploymentLogsResourceWithRawResponse(self._workers.deployment_logs)

    @cached_property
    def folders(self) -> AsyncFoldersResourceWithRawResponse:
        return AsyncFoldersResourceWithRawResponse(self._workers.folders)

    @cached_property
    def business_hours(self) -> AsyncBusinessHoursResourceWithRawResponse:
        return AsyncBusinessHoursResourceWithRawResponse(self._workers.business_hours)

    @cached_property
    def team_phone_hours(self) -> AsyncTeamPhoneHoursResourceWithRawResponse:
        return AsyncTeamPhoneHoursResourceWithRawResponse(self._workers.team_phone_hours)

    @cached_property
    def llm_logs(self) -> AsyncLlmLogsResourceWithRawResponse:
        return AsyncLlmLogsResourceWithRawResponse(self._workers.llm_logs)

    @cached_property
    def sessions(self) -> AsyncSessionsResourceWithRawResponse:
        return AsyncSessionsResourceWithRawResponse(self._workers.sessions)

    @cached_property
    def runtime_errors(self) -> AsyncRuntimeErrorsResourceWithRawResponse:
        return AsyncRuntimeErrorsResourceWithRawResponse(self._workers.runtime_errors)


class WorkersResourceWithStreamingResponse:
    def __init__(self, workers: WorkersResource) -> None:
        self._workers = workers

        self.create = to_streamed_response_wrapper(
            workers.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            workers.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            workers.update,
        )
        self.list = to_streamed_response_wrapper(
            workers.list,
        )
        self.delete = to_streamed_response_wrapper(
            workers.delete,
        )
        self.check_callable = to_streamed_response_wrapper(
            workers.check_callable,
        )
        self.retrieve_session = to_streamed_response_wrapper(
            workers.retrieve_session,
        )

    @cached_property
    def deployments(self) -> DeploymentsResourceWithStreamingResponse:
        return DeploymentsResourceWithStreamingResponse(self._workers.deployments)

    @cached_property
    def flows(self) -> FlowsResourceWithStreamingResponse:
        return FlowsResourceWithStreamingResponse(self._workers.flows)

    @cached_property
    def resources(self) -> ResourcesResourceWithStreamingResponse:
        return ResourcesResourceWithStreamingResponse(self._workers.resources)

    @cached_property
    def tests(self) -> TestsResourceWithStreamingResponse:
        return TestsResourceWithStreamingResponse(self._workers.tests)

    @cached_property
    def deployment_logs(self) -> DeploymentLogsResourceWithStreamingResponse:
        return DeploymentLogsResourceWithStreamingResponse(self._workers.deployment_logs)

    @cached_property
    def folders(self) -> FoldersResourceWithStreamingResponse:
        return FoldersResourceWithStreamingResponse(self._workers.folders)

    @cached_property
    def business_hours(self) -> BusinessHoursResourceWithStreamingResponse:
        return BusinessHoursResourceWithStreamingResponse(self._workers.business_hours)

    @cached_property
    def team_phone_hours(self) -> TeamPhoneHoursResourceWithStreamingResponse:
        return TeamPhoneHoursResourceWithStreamingResponse(self._workers.team_phone_hours)

    @cached_property
    def llm_logs(self) -> LlmLogsResourceWithStreamingResponse:
        return LlmLogsResourceWithStreamingResponse(self._workers.llm_logs)

    @cached_property
    def sessions(self) -> SessionsResourceWithStreamingResponse:
        return SessionsResourceWithStreamingResponse(self._workers.sessions)

    @cached_property
    def runtime_errors(self) -> RuntimeErrorsResourceWithStreamingResponse:
        return RuntimeErrorsResourceWithStreamingResponse(self._workers.runtime_errors)


class AsyncWorkersResourceWithStreamingResponse:
    def __init__(self, workers: AsyncWorkersResource) -> None:
        self._workers = workers

        self.create = async_to_streamed_response_wrapper(
            workers.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            workers.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            workers.update,
        )
        self.list = async_to_streamed_response_wrapper(
            workers.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            workers.delete,
        )
        self.check_callable = async_to_streamed_response_wrapper(
            workers.check_callable,
        )
        self.retrieve_session = async_to_streamed_response_wrapper(
            workers.retrieve_session,
        )

    @cached_property
    def deployments(self) -> AsyncDeploymentsResourceWithStreamingResponse:
        return AsyncDeploymentsResourceWithStreamingResponse(self._workers.deployments)

    @cached_property
    def flows(self) -> AsyncFlowsResourceWithStreamingResponse:
        return AsyncFlowsResourceWithStreamingResponse(self._workers.flows)

    @cached_property
    def resources(self) -> AsyncResourcesResourceWithStreamingResponse:
        return AsyncResourcesResourceWithStreamingResponse(self._workers.resources)

    @cached_property
    def tests(self) -> AsyncTestsResourceWithStreamingResponse:
        return AsyncTestsResourceWithStreamingResponse(self._workers.tests)

    @cached_property
    def deployment_logs(self) -> AsyncDeploymentLogsResourceWithStreamingResponse:
        return AsyncDeploymentLogsResourceWithStreamingResponse(self._workers.deployment_logs)

    @cached_property
    def folders(self) -> AsyncFoldersResourceWithStreamingResponse:
        return AsyncFoldersResourceWithStreamingResponse(self._workers.folders)

    @cached_property
    def business_hours(self) -> AsyncBusinessHoursResourceWithStreamingResponse:
        return AsyncBusinessHoursResourceWithStreamingResponse(self._workers.business_hours)

    @cached_property
    def team_phone_hours(self) -> AsyncTeamPhoneHoursResourceWithStreamingResponse:
        return AsyncTeamPhoneHoursResourceWithStreamingResponse(self._workers.team_phone_hours)

    @cached_property
    def llm_logs(self) -> AsyncLlmLogsResourceWithStreamingResponse:
        return AsyncLlmLogsResourceWithStreamingResponse(self._workers.llm_logs)

    @cached_property
    def sessions(self) -> AsyncSessionsResourceWithStreamingResponse:
        return AsyncSessionsResourceWithStreamingResponse(self._workers.sessions)

    @cached_property
    def runtime_errors(self) -> AsyncRuntimeErrorsResourceWithStreamingResponse:
        return AsyncRuntimeErrorsResourceWithStreamingResponse(self._workers.runtime_errors)

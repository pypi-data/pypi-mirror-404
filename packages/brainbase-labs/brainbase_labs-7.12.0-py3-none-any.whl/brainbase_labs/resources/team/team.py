# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .assets import (
    AssetsResource,
    AsyncAssetsResource,
    AssetsResourceWithRawResponse,
    AsyncAssetsResourceWithRawResponse,
    AssetsResourceWithStreamingResponse,
    AsyncAssetsResourceWithStreamingResponse,
)
from ...types import team_retrieve_params
from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .custom_voices import (
    CustomVoicesResource,
    AsyncCustomVoicesResource,
    CustomVoicesResourceWithRawResponse,
    AsyncCustomVoicesResourceWithRawResponse,
    CustomVoicesResourceWithStreamingResponse,
    AsyncCustomVoicesResourceWithStreamingResponse,
)
from ..._base_client import make_request_options
from .default_checks import (
    DefaultChecksResource,
    AsyncDefaultChecksResource,
    DefaultChecksResourceWithRawResponse,
    AsyncDefaultChecksResourceWithRawResponse,
    DefaultChecksResourceWithStreamingResponse,
    AsyncDefaultChecksResourceWithStreamingResponse,
)
from .integrations.integrations import (
    IntegrationsResource,
    AsyncIntegrationsResource,
    IntegrationsResourceWithRawResponse,
    AsyncIntegrationsResourceWithRawResponse,
    IntegrationsResourceWithStreamingResponse,
    AsyncIntegrationsResourceWithStreamingResponse,
)
from ...types.team_retrieve_response import TeamRetrieveResponse
from ...types.team_retrieve_subaccount_credentials_response import TeamRetrieveSubaccountCredentialsResponse

__all__ = ["TeamResource", "AsyncTeamResource"]


class TeamResource(SyncAPIResource):
    @cached_property
    def assets(self) -> AssetsResource:
        return AssetsResource(self._client)

    @cached_property
    def integrations(self) -> IntegrationsResource:
        return IntegrationsResource(self._client)

    @cached_property
    def default_checks(self) -> DefaultChecksResource:
        return DefaultChecksResource(self._client)

    @cached_property
    def custom_voices(self) -> CustomVoicesResource:
        return CustomVoicesResource(self._client)

    @cached_property
    def with_raw_response(self) -> TeamResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return TeamResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TeamResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return TeamResourceWithStreamingResponse(self)

    def retrieve(
        self,
        *,
        include_integrations: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TeamRetrieveResponse:
        """
        Get the team associated with the provided API key

        Args:
          include_integrations: Set to true to also include integrations in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/api/team",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"include_integrations": include_integrations}, team_retrieve_params.TeamRetrieveParams
                ),
            ),
            cast_to=TeamRetrieveResponse,
        )

    def retrieve_subaccount_credentials(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TeamRetrieveSubaccountCredentialsResponse:
        """Returns the team's Twilio subaccount SID and auth token.

        Used by workers for
        Brainbase-purchased phone numbers (integrationId is null).
        """
        return self._get(
            "/api/team/subaccount-credentials",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TeamRetrieveSubaccountCredentialsResponse,
        )


class AsyncTeamResource(AsyncAPIResource):
    @cached_property
    def assets(self) -> AsyncAssetsResource:
        return AsyncAssetsResource(self._client)

    @cached_property
    def integrations(self) -> AsyncIntegrationsResource:
        return AsyncIntegrationsResource(self._client)

    @cached_property
    def default_checks(self) -> AsyncDefaultChecksResource:
        return AsyncDefaultChecksResource(self._client)

    @cached_property
    def custom_voices(self) -> AsyncCustomVoicesResource:
        return AsyncCustomVoicesResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncTeamResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncTeamResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTeamResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncTeamResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        *,
        include_integrations: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TeamRetrieveResponse:
        """
        Get the team associated with the provided API key

        Args:
          include_integrations: Set to true to also include integrations in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/api/team",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"include_integrations": include_integrations}, team_retrieve_params.TeamRetrieveParams
                ),
            ),
            cast_to=TeamRetrieveResponse,
        )

    async def retrieve_subaccount_credentials(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TeamRetrieveSubaccountCredentialsResponse:
        """Returns the team's Twilio subaccount SID and auth token.

        Used by workers for
        Brainbase-purchased phone numbers (integrationId is null).
        """
        return await self._get(
            "/api/team/subaccount-credentials",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TeamRetrieveSubaccountCredentialsResponse,
        )


class TeamResourceWithRawResponse:
    def __init__(self, team: TeamResource) -> None:
        self._team = team

        self.retrieve = to_raw_response_wrapper(
            team.retrieve,
        )
        self.retrieve_subaccount_credentials = to_raw_response_wrapper(
            team.retrieve_subaccount_credentials,
        )

    @cached_property
    def assets(self) -> AssetsResourceWithRawResponse:
        return AssetsResourceWithRawResponse(self._team.assets)

    @cached_property
    def integrations(self) -> IntegrationsResourceWithRawResponse:
        return IntegrationsResourceWithRawResponse(self._team.integrations)

    @cached_property
    def default_checks(self) -> DefaultChecksResourceWithRawResponse:
        return DefaultChecksResourceWithRawResponse(self._team.default_checks)

    @cached_property
    def custom_voices(self) -> CustomVoicesResourceWithRawResponse:
        return CustomVoicesResourceWithRawResponse(self._team.custom_voices)


class AsyncTeamResourceWithRawResponse:
    def __init__(self, team: AsyncTeamResource) -> None:
        self._team = team

        self.retrieve = async_to_raw_response_wrapper(
            team.retrieve,
        )
        self.retrieve_subaccount_credentials = async_to_raw_response_wrapper(
            team.retrieve_subaccount_credentials,
        )

    @cached_property
    def assets(self) -> AsyncAssetsResourceWithRawResponse:
        return AsyncAssetsResourceWithRawResponse(self._team.assets)

    @cached_property
    def integrations(self) -> AsyncIntegrationsResourceWithRawResponse:
        return AsyncIntegrationsResourceWithRawResponse(self._team.integrations)

    @cached_property
    def default_checks(self) -> AsyncDefaultChecksResourceWithRawResponse:
        return AsyncDefaultChecksResourceWithRawResponse(self._team.default_checks)

    @cached_property
    def custom_voices(self) -> AsyncCustomVoicesResourceWithRawResponse:
        return AsyncCustomVoicesResourceWithRawResponse(self._team.custom_voices)


class TeamResourceWithStreamingResponse:
    def __init__(self, team: TeamResource) -> None:
        self._team = team

        self.retrieve = to_streamed_response_wrapper(
            team.retrieve,
        )
        self.retrieve_subaccount_credentials = to_streamed_response_wrapper(
            team.retrieve_subaccount_credentials,
        )

    @cached_property
    def assets(self) -> AssetsResourceWithStreamingResponse:
        return AssetsResourceWithStreamingResponse(self._team.assets)

    @cached_property
    def integrations(self) -> IntegrationsResourceWithStreamingResponse:
        return IntegrationsResourceWithStreamingResponse(self._team.integrations)

    @cached_property
    def default_checks(self) -> DefaultChecksResourceWithStreamingResponse:
        return DefaultChecksResourceWithStreamingResponse(self._team.default_checks)

    @cached_property
    def custom_voices(self) -> CustomVoicesResourceWithStreamingResponse:
        return CustomVoicesResourceWithStreamingResponse(self._team.custom_voices)


class AsyncTeamResourceWithStreamingResponse:
    def __init__(self, team: AsyncTeamResource) -> None:
        self._team = team

        self.retrieve = async_to_streamed_response_wrapper(
            team.retrieve,
        )
        self.retrieve_subaccount_credentials = async_to_streamed_response_wrapper(
            team.retrieve_subaccount_credentials,
        )

    @cached_property
    def assets(self) -> AsyncAssetsResourceWithStreamingResponse:
        return AsyncAssetsResourceWithStreamingResponse(self._team.assets)

    @cached_property
    def integrations(self) -> AsyncIntegrationsResourceWithStreamingResponse:
        return AsyncIntegrationsResourceWithStreamingResponse(self._team.integrations)

    @cached_property
    def default_checks(self) -> AsyncDefaultChecksResourceWithStreamingResponse:
        return AsyncDefaultChecksResourceWithStreamingResponse(self._team.default_checks)

    @cached_property
    def custom_voices(self) -> AsyncCustomVoicesResourceWithStreamingResponse:
        return AsyncCustomVoicesResourceWithStreamingResponse(self._team.custom_voices)

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .chat.chat import (
    ChatResource,
    AsyncChatResource,
    ChatResourceWithRawResponse,
    AsyncChatResourceWithRawResponse,
    ChatResourceWithStreamingResponse,
    AsyncChatResourceWithStreamingResponse,
)
from ...._compat import cached_property
from .voice.voice import (
    VoiceResource,
    AsyncVoiceResource,
    VoiceResourceWithRawResponse,
    AsyncVoiceResourceWithRawResponse,
    VoiceResourceWithStreamingResponse,
    AsyncVoiceResourceWithStreamingResponse,
)
from ...._resource import SyncAPIResource, AsyncAPIResource
from .default_checks import (
    DefaultChecksResource,
    AsyncDefaultChecksResource,
    DefaultChecksResourceWithRawResponse,
    AsyncDefaultChecksResourceWithRawResponse,
    DefaultChecksResourceWithStreamingResponse,
    AsyncDefaultChecksResourceWithStreamingResponse,
)
from .voicev1.voicev1 import (
    Voicev1Resource,
    AsyncVoicev1Resource,
    Voicev1ResourceWithRawResponse,
    AsyncVoicev1ResourceWithRawResponse,
    Voicev1ResourceWithStreamingResponse,
    AsyncVoicev1ResourceWithStreamingResponse,
)

__all__ = ["DeploymentsResource", "AsyncDeploymentsResource"]


class DeploymentsResource(SyncAPIResource):
    @cached_property
    def voice(self) -> VoiceResource:
        return VoiceResource(self._client)

    @cached_property
    def voicev1(self) -> Voicev1Resource:
        return Voicev1Resource(self._client)

    @cached_property
    def chat(self) -> ChatResource:
        return ChatResource(self._client)

    @cached_property
    def default_checks(self) -> DefaultChecksResource:
        return DefaultChecksResource(self._client)

    @cached_property
    def with_raw_response(self) -> DeploymentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return DeploymentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DeploymentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return DeploymentsResourceWithStreamingResponse(self)


class AsyncDeploymentsResource(AsyncAPIResource):
    @cached_property
    def voice(self) -> AsyncVoiceResource:
        return AsyncVoiceResource(self._client)

    @cached_property
    def voicev1(self) -> AsyncVoicev1Resource:
        return AsyncVoicev1Resource(self._client)

    @cached_property
    def chat(self) -> AsyncChatResource:
        return AsyncChatResource(self._client)

    @cached_property
    def default_checks(self) -> AsyncDefaultChecksResource:
        return AsyncDefaultChecksResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncDeploymentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncDeploymentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDeploymentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncDeploymentsResourceWithStreamingResponse(self)


class DeploymentsResourceWithRawResponse:
    def __init__(self, deployments: DeploymentsResource) -> None:
        self._deployments = deployments

    @cached_property
    def voice(self) -> VoiceResourceWithRawResponse:
        return VoiceResourceWithRawResponse(self._deployments.voice)

    @cached_property
    def voicev1(self) -> Voicev1ResourceWithRawResponse:
        return Voicev1ResourceWithRawResponse(self._deployments.voicev1)

    @cached_property
    def chat(self) -> ChatResourceWithRawResponse:
        return ChatResourceWithRawResponse(self._deployments.chat)

    @cached_property
    def default_checks(self) -> DefaultChecksResourceWithRawResponse:
        return DefaultChecksResourceWithRawResponse(self._deployments.default_checks)


class AsyncDeploymentsResourceWithRawResponse:
    def __init__(self, deployments: AsyncDeploymentsResource) -> None:
        self._deployments = deployments

    @cached_property
    def voice(self) -> AsyncVoiceResourceWithRawResponse:
        return AsyncVoiceResourceWithRawResponse(self._deployments.voice)

    @cached_property
    def voicev1(self) -> AsyncVoicev1ResourceWithRawResponse:
        return AsyncVoicev1ResourceWithRawResponse(self._deployments.voicev1)

    @cached_property
    def chat(self) -> AsyncChatResourceWithRawResponse:
        return AsyncChatResourceWithRawResponse(self._deployments.chat)

    @cached_property
    def default_checks(self) -> AsyncDefaultChecksResourceWithRawResponse:
        return AsyncDefaultChecksResourceWithRawResponse(self._deployments.default_checks)


class DeploymentsResourceWithStreamingResponse:
    def __init__(self, deployments: DeploymentsResource) -> None:
        self._deployments = deployments

    @cached_property
    def voice(self) -> VoiceResourceWithStreamingResponse:
        return VoiceResourceWithStreamingResponse(self._deployments.voice)

    @cached_property
    def voicev1(self) -> Voicev1ResourceWithStreamingResponse:
        return Voicev1ResourceWithStreamingResponse(self._deployments.voicev1)

    @cached_property
    def chat(self) -> ChatResourceWithStreamingResponse:
        return ChatResourceWithStreamingResponse(self._deployments.chat)

    @cached_property
    def default_checks(self) -> DefaultChecksResourceWithStreamingResponse:
        return DefaultChecksResourceWithStreamingResponse(self._deployments.default_checks)


class AsyncDeploymentsResourceWithStreamingResponse:
    def __init__(self, deployments: AsyncDeploymentsResource) -> None:
        self._deployments = deployments

    @cached_property
    def voice(self) -> AsyncVoiceResourceWithStreamingResponse:
        return AsyncVoiceResourceWithStreamingResponse(self._deployments.voice)

    @cached_property
    def voicev1(self) -> AsyncVoicev1ResourceWithStreamingResponse:
        return AsyncVoicev1ResourceWithStreamingResponse(self._deployments.voicev1)

    @cached_property
    def chat(self) -> AsyncChatResourceWithStreamingResponse:
        return AsyncChatResourceWithStreamingResponse(self._deployments.chat)

    @cached_property
    def default_checks(self) -> AsyncDefaultChecksResourceWithStreamingResponse:
        return AsyncDefaultChecksResourceWithStreamingResponse(self._deployments.default_checks)

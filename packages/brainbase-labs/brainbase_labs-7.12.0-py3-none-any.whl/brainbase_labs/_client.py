# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Mapping
from typing_extensions import Self, override

import httpx

from . import _exceptions
from ._qs import Querystring
from ._types import (
    Omit,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
    not_given,
)
from ._utils import is_given, get_async_library
from ._compat import cached_property
from ._version import __version__
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import APIStatusError, BrainbaseLabsError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import team, workers, portkey_logs, voice_analysis
    from .resources.team.team import TeamResource, AsyncTeamResource
    from .resources.portkey_logs import PortkeyLogsResource, AsyncPortkeyLogsResource
    from .resources.voice_analysis import VoiceAnalysisResource, AsyncVoiceAnalysisResource
    from .resources.workers.workers import WorkersResource, AsyncWorkersResource

__all__ = [
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "BrainbaseLabs",
    "AsyncBrainbaseLabs",
    "Client",
    "AsyncClient",
]


class BrainbaseLabs(SyncAPIClient):
    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new synchronous BrainbaseLabs client instance.

        This automatically infers the `api_key` argument from the `BRAINBASE_LABS_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("BRAINBASE_LABS_API_KEY")
        if api_key is None:
            raise BrainbaseLabsError(
                "The api_key client option must be set either by passing api_key to the client or by setting the BRAINBASE_LABS_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("BRAINBASE_LABS_BASE_URL")
        if base_url is None:
            base_url = f"https://brainbase-monorepo-api.onrender.com"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def team(self) -> TeamResource:
        from .resources.team import TeamResource

        return TeamResource(self)

    @cached_property
    def workers(self) -> WorkersResource:
        from .resources.workers import WorkersResource

        return WorkersResource(self)

    @cached_property
    def voice_analysis(self) -> VoiceAnalysisResource:
        from .resources.voice_analysis import VoiceAnalysisResource

        return VoiceAnalysisResource(self)

    @cached_property
    def portkey_logs(self) -> PortkeyLogsResource:
        from .resources.portkey_logs import PortkeyLogsResource

        return PortkeyLogsResource(self)

    @cached_property
    def with_raw_response(self) -> BrainbaseLabsWithRawResponse:
        return BrainbaseLabsWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> BrainbaseLabsWithStreamedResponse:
        return BrainbaseLabsWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"x-api-key": api_key}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class AsyncBrainbaseLabs(AsyncAPIClient):
    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultAsyncHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.AsyncClient | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new async AsyncBrainbaseLabs client instance.

        This automatically infers the `api_key` argument from the `BRAINBASE_LABS_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("BRAINBASE_LABS_API_KEY")
        if api_key is None:
            raise BrainbaseLabsError(
                "The api_key client option must be set either by passing api_key to the client or by setting the BRAINBASE_LABS_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("BRAINBASE_LABS_BASE_URL")
        if base_url is None:
            base_url = f"https://brainbase-monorepo-api.onrender.com"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def team(self) -> AsyncTeamResource:
        from .resources.team import AsyncTeamResource

        return AsyncTeamResource(self)

    @cached_property
    def workers(self) -> AsyncWorkersResource:
        from .resources.workers import AsyncWorkersResource

        return AsyncWorkersResource(self)

    @cached_property
    def voice_analysis(self) -> AsyncVoiceAnalysisResource:
        from .resources.voice_analysis import AsyncVoiceAnalysisResource

        return AsyncVoiceAnalysisResource(self)

    @cached_property
    def portkey_logs(self) -> AsyncPortkeyLogsResource:
        from .resources.portkey_logs import AsyncPortkeyLogsResource

        return AsyncPortkeyLogsResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncBrainbaseLabsWithRawResponse:
        return AsyncBrainbaseLabsWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncBrainbaseLabsWithStreamedResponse:
        return AsyncBrainbaseLabsWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"x-api-key": api_key}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class BrainbaseLabsWithRawResponse:
    _client: BrainbaseLabs

    def __init__(self, client: BrainbaseLabs) -> None:
        self._client = client

    @cached_property
    def team(self) -> team.TeamResourceWithRawResponse:
        from .resources.team import TeamResourceWithRawResponse

        return TeamResourceWithRawResponse(self._client.team)

    @cached_property
    def workers(self) -> workers.WorkersResourceWithRawResponse:
        from .resources.workers import WorkersResourceWithRawResponse

        return WorkersResourceWithRawResponse(self._client.workers)

    @cached_property
    def voice_analysis(self) -> voice_analysis.VoiceAnalysisResourceWithRawResponse:
        from .resources.voice_analysis import VoiceAnalysisResourceWithRawResponse

        return VoiceAnalysisResourceWithRawResponse(self._client.voice_analysis)

    @cached_property
    def portkey_logs(self) -> portkey_logs.PortkeyLogsResourceWithRawResponse:
        from .resources.portkey_logs import PortkeyLogsResourceWithRawResponse

        return PortkeyLogsResourceWithRawResponse(self._client.portkey_logs)


class AsyncBrainbaseLabsWithRawResponse:
    _client: AsyncBrainbaseLabs

    def __init__(self, client: AsyncBrainbaseLabs) -> None:
        self._client = client

    @cached_property
    def team(self) -> team.AsyncTeamResourceWithRawResponse:
        from .resources.team import AsyncTeamResourceWithRawResponse

        return AsyncTeamResourceWithRawResponse(self._client.team)

    @cached_property
    def workers(self) -> workers.AsyncWorkersResourceWithRawResponse:
        from .resources.workers import AsyncWorkersResourceWithRawResponse

        return AsyncWorkersResourceWithRawResponse(self._client.workers)

    @cached_property
    def voice_analysis(self) -> voice_analysis.AsyncVoiceAnalysisResourceWithRawResponse:
        from .resources.voice_analysis import AsyncVoiceAnalysisResourceWithRawResponse

        return AsyncVoiceAnalysisResourceWithRawResponse(self._client.voice_analysis)

    @cached_property
    def portkey_logs(self) -> portkey_logs.AsyncPortkeyLogsResourceWithRawResponse:
        from .resources.portkey_logs import AsyncPortkeyLogsResourceWithRawResponse

        return AsyncPortkeyLogsResourceWithRawResponse(self._client.portkey_logs)


class BrainbaseLabsWithStreamedResponse:
    _client: BrainbaseLabs

    def __init__(self, client: BrainbaseLabs) -> None:
        self._client = client

    @cached_property
    def team(self) -> team.TeamResourceWithStreamingResponse:
        from .resources.team import TeamResourceWithStreamingResponse

        return TeamResourceWithStreamingResponse(self._client.team)

    @cached_property
    def workers(self) -> workers.WorkersResourceWithStreamingResponse:
        from .resources.workers import WorkersResourceWithStreamingResponse

        return WorkersResourceWithStreamingResponse(self._client.workers)

    @cached_property
    def voice_analysis(self) -> voice_analysis.VoiceAnalysisResourceWithStreamingResponse:
        from .resources.voice_analysis import VoiceAnalysisResourceWithStreamingResponse

        return VoiceAnalysisResourceWithStreamingResponse(self._client.voice_analysis)

    @cached_property
    def portkey_logs(self) -> portkey_logs.PortkeyLogsResourceWithStreamingResponse:
        from .resources.portkey_logs import PortkeyLogsResourceWithStreamingResponse

        return PortkeyLogsResourceWithStreamingResponse(self._client.portkey_logs)


class AsyncBrainbaseLabsWithStreamedResponse:
    _client: AsyncBrainbaseLabs

    def __init__(self, client: AsyncBrainbaseLabs) -> None:
        self._client = client

    @cached_property
    def team(self) -> team.AsyncTeamResourceWithStreamingResponse:
        from .resources.team import AsyncTeamResourceWithStreamingResponse

        return AsyncTeamResourceWithStreamingResponse(self._client.team)

    @cached_property
    def workers(self) -> workers.AsyncWorkersResourceWithStreamingResponse:
        from .resources.workers import AsyncWorkersResourceWithStreamingResponse

        return AsyncWorkersResourceWithStreamingResponse(self._client.workers)

    @cached_property
    def voice_analysis(self) -> voice_analysis.AsyncVoiceAnalysisResourceWithStreamingResponse:
        from .resources.voice_analysis import AsyncVoiceAnalysisResourceWithStreamingResponse

        return AsyncVoiceAnalysisResourceWithStreamingResponse(self._client.voice_analysis)

    @cached_property
    def portkey_logs(self) -> portkey_logs.AsyncPortkeyLogsResourceWithStreamingResponse:
        from .resources.portkey_logs import AsyncPortkeyLogsResourceWithStreamingResponse

        return AsyncPortkeyLogsResourceWithStreamingResponse(self._client.portkey_logs)


Client = BrainbaseLabs

AsyncClient = AsyncBrainbaseLabs

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from brainbase_labs import BrainbaseLabs, AsyncBrainbaseLabs
from brainbase_labs.types import TeamRetrieveResponse, TeamRetrieveSubaccountCredentialsResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTeam:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: BrainbaseLabs) -> None:
        team = client.team.retrieve()
        assert_matches_type(TeamRetrieveResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_with_all_params(self, client: BrainbaseLabs) -> None:
        team = client.team.retrieve(
            include_integrations=True,
        )
        assert_matches_type(TeamRetrieveResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: BrainbaseLabs) -> None:
        response = client.team.with_raw_response.retrieve()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = response.parse()
        assert_matches_type(TeamRetrieveResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: BrainbaseLabs) -> None:
        with client.team.with_streaming_response.retrieve() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = response.parse()
            assert_matches_type(TeamRetrieveResponse, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_subaccount_credentials(self, client: BrainbaseLabs) -> None:
        team = client.team.retrieve_subaccount_credentials()
        assert_matches_type(TeamRetrieveSubaccountCredentialsResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_subaccount_credentials(self, client: BrainbaseLabs) -> None:
        response = client.team.with_raw_response.retrieve_subaccount_credentials()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = response.parse()
        assert_matches_type(TeamRetrieveSubaccountCredentialsResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_subaccount_credentials(self, client: BrainbaseLabs) -> None:
        with client.team.with_streaming_response.retrieve_subaccount_credentials() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = response.parse()
            assert_matches_type(TeamRetrieveSubaccountCredentialsResponse, team, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncTeam:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        team = await async_client.team.retrieve()
        assert_matches_type(TeamRetrieveResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        team = await async_client.team.retrieve(
            include_integrations=True,
        )
        assert_matches_type(TeamRetrieveResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.team.with_raw_response.retrieve()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = await response.parse()
        assert_matches_type(TeamRetrieveResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.team.with_streaming_response.retrieve() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = await response.parse()
            assert_matches_type(TeamRetrieveResponse, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_subaccount_credentials(self, async_client: AsyncBrainbaseLabs) -> None:
        team = await async_client.team.retrieve_subaccount_credentials()
        assert_matches_type(TeamRetrieveSubaccountCredentialsResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_subaccount_credentials(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.team.with_raw_response.retrieve_subaccount_credentials()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = await response.parse()
        assert_matches_type(TeamRetrieveSubaccountCredentialsResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_subaccount_credentials(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.team.with_streaming_response.retrieve_subaccount_credentials() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = await response.parse()
            assert_matches_type(TeamRetrieveSubaccountCredentialsResponse, team, path=["response"])

        assert cast(Any, response.is_closed) is True

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from brainbase_labs import BrainbaseLabs, AsyncBrainbaseLabs
from brainbase_labs.types.shared import Integration

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTwilio:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: BrainbaseLabs) -> None:
        twilio = client.team.integrations.twilio.create(
            account_sid="accountSid",
            auth_token="authToken",
        )
        assert_matches_type(Integration, twilio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: BrainbaseLabs) -> None:
        twilio = client.team.integrations.twilio.create(
            account_sid="accountSid",
            auth_token="authToken",
            description="description",
            name="name",
        )
        assert_matches_type(Integration, twilio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: BrainbaseLabs) -> None:
        response = client.team.integrations.twilio.with_raw_response.create(
            account_sid="accountSid",
            auth_token="authToken",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        twilio = response.parse()
        assert_matches_type(Integration, twilio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: BrainbaseLabs) -> None:
        with client.team.integrations.twilio.with_streaming_response.create(
            account_sid="accountSid",
            auth_token="authToken",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            twilio = response.parse()
            assert_matches_type(Integration, twilio, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: BrainbaseLabs) -> None:
        twilio = client.team.integrations.twilio.delete(
            "integrationId",
        )
        assert twilio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: BrainbaseLabs) -> None:
        response = client.team.integrations.twilio.with_raw_response.delete(
            "integrationId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        twilio = response.parse()
        assert twilio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: BrainbaseLabs) -> None:
        with client.team.integrations.twilio.with_streaming_response.delete(
            "integrationId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            twilio = response.parse()
            assert twilio is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `integration_id` but received ''"):
            client.team.integrations.twilio.with_raw_response.delete(
                "",
            )


class TestAsyncTwilio:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncBrainbaseLabs) -> None:
        twilio = await async_client.team.integrations.twilio.create(
            account_sid="accountSid",
            auth_token="authToken",
        )
        assert_matches_type(Integration, twilio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        twilio = await async_client.team.integrations.twilio.create(
            account_sid="accountSid",
            auth_token="authToken",
            description="description",
            name="name",
        )
        assert_matches_type(Integration, twilio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.team.integrations.twilio.with_raw_response.create(
            account_sid="accountSid",
            auth_token="authToken",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        twilio = await response.parse()
        assert_matches_type(Integration, twilio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.team.integrations.twilio.with_streaming_response.create(
            account_sid="accountSid",
            auth_token="authToken",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            twilio = await response.parse()
            assert_matches_type(Integration, twilio, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        twilio = await async_client.team.integrations.twilio.delete(
            "integrationId",
        )
        assert twilio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.team.integrations.twilio.with_raw_response.delete(
            "integrationId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        twilio = await response.parse()
        assert twilio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.team.integrations.twilio.with_streaming_response.delete(
            "integrationId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            twilio = await response.parse()
            assert twilio is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `integration_id` but received ''"):
            await async_client.team.integrations.twilio.with_raw_response.delete(
                "",
            )

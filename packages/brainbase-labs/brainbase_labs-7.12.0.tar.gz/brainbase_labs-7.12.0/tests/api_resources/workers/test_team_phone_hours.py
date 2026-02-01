# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from brainbase_labs import BrainbaseLabs, AsyncBrainbaseLabs
from brainbase_labs.types.workers import (
    TeamPhoneHourListResponse,
    TeamPhoneHourCreateResponse,
    TeamPhoneHourUpdateResponse,
    TeamPhoneHourRetrieveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTeamPhoneHours:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: BrainbaseLabs) -> None:
        team_phone_hour = client.workers.team_phone_hours.create(
            hours_id="hoursId",
            phone_number="phoneNumber",
            team_id="teamId",
        )
        assert_matches_type(TeamPhoneHourCreateResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: BrainbaseLabs) -> None:
        response = client.workers.team_phone_hours.with_raw_response.create(
            hours_id="hoursId",
            phone_number="phoneNumber",
            team_id="teamId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team_phone_hour = response.parse()
        assert_matches_type(TeamPhoneHourCreateResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: BrainbaseLabs) -> None:
        with client.workers.team_phone_hours.with_streaming_response.create(
            hours_id="hoursId",
            phone_number="phoneNumber",
            team_id="teamId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team_phone_hour = response.parse()
            assert_matches_type(TeamPhoneHourCreateResponse, team_phone_hour, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: BrainbaseLabs) -> None:
        team_phone_hour = client.workers.team_phone_hours.retrieve(
            id="id",
        )
        assert_matches_type(TeamPhoneHourRetrieveResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_with_all_params(self, client: BrainbaseLabs) -> None:
        team_phone_hour = client.workers.team_phone_hours.retrieve(
            id="id",
            include_relations=True,
        )
        assert_matches_type(TeamPhoneHourRetrieveResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: BrainbaseLabs) -> None:
        response = client.workers.team_phone_hours.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team_phone_hour = response.parse()
        assert_matches_type(TeamPhoneHourRetrieveResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: BrainbaseLabs) -> None:
        with client.workers.team_phone_hours.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team_phone_hour = response.parse()
            assert_matches_type(TeamPhoneHourRetrieveResponse, team_phone_hour, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.workers.team_phone_hours.with_raw_response.retrieve(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: BrainbaseLabs) -> None:
        team_phone_hour = client.workers.team_phone_hours.update(
            id="id",
        )
        assert_matches_type(TeamPhoneHourUpdateResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: BrainbaseLabs) -> None:
        team_phone_hour = client.workers.team_phone_hours.update(
            id="id",
            hours_id="hoursId",
            phone_number="phoneNumber",
            team_id="teamId",
        )
        assert_matches_type(TeamPhoneHourUpdateResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: BrainbaseLabs) -> None:
        response = client.workers.team_phone_hours.with_raw_response.update(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team_phone_hour = response.parse()
        assert_matches_type(TeamPhoneHourUpdateResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: BrainbaseLabs) -> None:
        with client.workers.team_phone_hours.with_streaming_response.update(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team_phone_hour = response.parse()
            assert_matches_type(TeamPhoneHourUpdateResponse, team_phone_hour, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.workers.team_phone_hours.with_raw_response.update(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: BrainbaseLabs) -> None:
        team_phone_hour = client.workers.team_phone_hours.list()
        assert_matches_type(TeamPhoneHourListResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: BrainbaseLabs) -> None:
        team_phone_hour = client.workers.team_phone_hours.list(
            include_relations=True,
            phone_number="phoneNumber",
            team_id="teamId",
        )
        assert_matches_type(TeamPhoneHourListResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: BrainbaseLabs) -> None:
        response = client.workers.team_phone_hours.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team_phone_hour = response.parse()
        assert_matches_type(TeamPhoneHourListResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: BrainbaseLabs) -> None:
        with client.workers.team_phone_hours.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team_phone_hour = response.parse()
            assert_matches_type(TeamPhoneHourListResponse, team_phone_hour, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: BrainbaseLabs) -> None:
        team_phone_hour = client.workers.team_phone_hours.delete(
            "id",
        )
        assert team_phone_hour is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: BrainbaseLabs) -> None:
        response = client.workers.team_phone_hours.with_raw_response.delete(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team_phone_hour = response.parse()
        assert team_phone_hour is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: BrainbaseLabs) -> None:
        with client.workers.team_phone_hours.with_streaming_response.delete(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team_phone_hour = response.parse()
            assert team_phone_hour is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.workers.team_phone_hours.with_raw_response.delete(
                "",
            )


class TestAsyncTeamPhoneHours:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncBrainbaseLabs) -> None:
        team_phone_hour = await async_client.workers.team_phone_hours.create(
            hours_id="hoursId",
            phone_number="phoneNumber",
            team_id="teamId",
        )
        assert_matches_type(TeamPhoneHourCreateResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.team_phone_hours.with_raw_response.create(
            hours_id="hoursId",
            phone_number="phoneNumber",
            team_id="teamId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team_phone_hour = await response.parse()
        assert_matches_type(TeamPhoneHourCreateResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.team_phone_hours.with_streaming_response.create(
            hours_id="hoursId",
            phone_number="phoneNumber",
            team_id="teamId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team_phone_hour = await response.parse()
            assert_matches_type(TeamPhoneHourCreateResponse, team_phone_hour, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        team_phone_hour = await async_client.workers.team_phone_hours.retrieve(
            id="id",
        )
        assert_matches_type(TeamPhoneHourRetrieveResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        team_phone_hour = await async_client.workers.team_phone_hours.retrieve(
            id="id",
            include_relations=True,
        )
        assert_matches_type(TeamPhoneHourRetrieveResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.team_phone_hours.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team_phone_hour = await response.parse()
        assert_matches_type(TeamPhoneHourRetrieveResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.team_phone_hours.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team_phone_hour = await response.parse()
            assert_matches_type(TeamPhoneHourRetrieveResponse, team_phone_hour, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.workers.team_phone_hours.with_raw_response.retrieve(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncBrainbaseLabs) -> None:
        team_phone_hour = await async_client.workers.team_phone_hours.update(
            id="id",
        )
        assert_matches_type(TeamPhoneHourUpdateResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        team_phone_hour = await async_client.workers.team_phone_hours.update(
            id="id",
            hours_id="hoursId",
            phone_number="phoneNumber",
            team_id="teamId",
        )
        assert_matches_type(TeamPhoneHourUpdateResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.team_phone_hours.with_raw_response.update(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team_phone_hour = await response.parse()
        assert_matches_type(TeamPhoneHourUpdateResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.team_phone_hours.with_streaming_response.update(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team_phone_hour = await response.parse()
            assert_matches_type(TeamPhoneHourUpdateResponse, team_phone_hour, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.workers.team_phone_hours.with_raw_response.update(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncBrainbaseLabs) -> None:
        team_phone_hour = await async_client.workers.team_phone_hours.list()
        assert_matches_type(TeamPhoneHourListResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        team_phone_hour = await async_client.workers.team_phone_hours.list(
            include_relations=True,
            phone_number="phoneNumber",
            team_id="teamId",
        )
        assert_matches_type(TeamPhoneHourListResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.team_phone_hours.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team_phone_hour = await response.parse()
        assert_matches_type(TeamPhoneHourListResponse, team_phone_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.team_phone_hours.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team_phone_hour = await response.parse()
            assert_matches_type(TeamPhoneHourListResponse, team_phone_hour, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        team_phone_hour = await async_client.workers.team_phone_hours.delete(
            "id",
        )
        assert team_phone_hour is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.team_phone_hours.with_raw_response.delete(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team_phone_hour = await response.parse()
        assert team_phone_hour is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.team_phone_hours.with_streaming_response.delete(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team_phone_hour = await response.parse()
            assert team_phone_hour is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.workers.team_phone_hours.with_raw_response.delete(
                "",
            )

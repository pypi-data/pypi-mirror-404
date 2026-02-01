# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from brainbase_labs import BrainbaseLabs, AsyncBrainbaseLabs
from brainbase_labs.types.workers import (
    BusinessHourListResponse,
    BusinessHourCreateResponse,
    BusinessHourUpdateResponse,
    BusinessHourRetrieveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestBusinessHours:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: BrainbaseLabs) -> None:
        business_hour = client.workers.business_hours.create(
            hours={"foo": "string"},
        )
        assert_matches_type(BusinessHourCreateResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: BrainbaseLabs) -> None:
        business_hour = client.workers.business_hours.create(
            hours={"foo": "string"},
            primary_tag="primaryTag",
            secondary_tag="secondaryTag",
            timezone="timezone",
        )
        assert_matches_type(BusinessHourCreateResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: BrainbaseLabs) -> None:
        response = client.workers.business_hours.with_raw_response.create(
            hours={"foo": "string"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        business_hour = response.parse()
        assert_matches_type(BusinessHourCreateResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: BrainbaseLabs) -> None:
        with client.workers.business_hours.with_streaming_response.create(
            hours={"foo": "string"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            business_hour = response.parse()
            assert_matches_type(BusinessHourCreateResponse, business_hour, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: BrainbaseLabs) -> None:
        business_hour = client.workers.business_hours.retrieve(
            id="id",
        )
        assert_matches_type(BusinessHourRetrieveResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_with_all_params(self, client: BrainbaseLabs) -> None:
        business_hour = client.workers.business_hours.retrieve(
            id="id",
            include_team_phone_hours=True,
        )
        assert_matches_type(BusinessHourRetrieveResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: BrainbaseLabs) -> None:
        response = client.workers.business_hours.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        business_hour = response.parse()
        assert_matches_type(BusinessHourRetrieveResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: BrainbaseLabs) -> None:
        with client.workers.business_hours.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            business_hour = response.parse()
            assert_matches_type(BusinessHourRetrieveResponse, business_hour, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.workers.business_hours.with_raw_response.retrieve(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: BrainbaseLabs) -> None:
        business_hour = client.workers.business_hours.update(
            id="id",
        )
        assert_matches_type(BusinessHourUpdateResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: BrainbaseLabs) -> None:
        business_hour = client.workers.business_hours.update(
            id="id",
            hours={"foo": "string"},
            primary_tag="primaryTag",
            secondary_tag="secondaryTag",
            timezone="timezone",
        )
        assert_matches_type(BusinessHourUpdateResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: BrainbaseLabs) -> None:
        response = client.workers.business_hours.with_raw_response.update(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        business_hour = response.parse()
        assert_matches_type(BusinessHourUpdateResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: BrainbaseLabs) -> None:
        with client.workers.business_hours.with_streaming_response.update(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            business_hour = response.parse()
            assert_matches_type(BusinessHourUpdateResponse, business_hour, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.workers.business_hours.with_raw_response.update(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: BrainbaseLabs) -> None:
        business_hour = client.workers.business_hours.list()
        assert_matches_type(BusinessHourListResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: BrainbaseLabs) -> None:
        business_hour = client.workers.business_hours.list(
            include_team_phone_hours=True,
        )
        assert_matches_type(BusinessHourListResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: BrainbaseLabs) -> None:
        response = client.workers.business_hours.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        business_hour = response.parse()
        assert_matches_type(BusinessHourListResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: BrainbaseLabs) -> None:
        with client.workers.business_hours.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            business_hour = response.parse()
            assert_matches_type(BusinessHourListResponse, business_hour, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: BrainbaseLabs) -> None:
        business_hour = client.workers.business_hours.delete(
            "id",
        )
        assert business_hour is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: BrainbaseLabs) -> None:
        response = client.workers.business_hours.with_raw_response.delete(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        business_hour = response.parse()
        assert business_hour is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: BrainbaseLabs) -> None:
        with client.workers.business_hours.with_streaming_response.delete(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            business_hour = response.parse()
            assert business_hour is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.workers.business_hours.with_raw_response.delete(
                "",
            )


class TestAsyncBusinessHours:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncBrainbaseLabs) -> None:
        business_hour = await async_client.workers.business_hours.create(
            hours={"foo": "string"},
        )
        assert_matches_type(BusinessHourCreateResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        business_hour = await async_client.workers.business_hours.create(
            hours={"foo": "string"},
            primary_tag="primaryTag",
            secondary_tag="secondaryTag",
            timezone="timezone",
        )
        assert_matches_type(BusinessHourCreateResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.business_hours.with_raw_response.create(
            hours={"foo": "string"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        business_hour = await response.parse()
        assert_matches_type(BusinessHourCreateResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.business_hours.with_streaming_response.create(
            hours={"foo": "string"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            business_hour = await response.parse()
            assert_matches_type(BusinessHourCreateResponse, business_hour, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        business_hour = await async_client.workers.business_hours.retrieve(
            id="id",
        )
        assert_matches_type(BusinessHourRetrieveResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        business_hour = await async_client.workers.business_hours.retrieve(
            id="id",
            include_team_phone_hours=True,
        )
        assert_matches_type(BusinessHourRetrieveResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.business_hours.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        business_hour = await response.parse()
        assert_matches_type(BusinessHourRetrieveResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.business_hours.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            business_hour = await response.parse()
            assert_matches_type(BusinessHourRetrieveResponse, business_hour, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.workers.business_hours.with_raw_response.retrieve(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncBrainbaseLabs) -> None:
        business_hour = await async_client.workers.business_hours.update(
            id="id",
        )
        assert_matches_type(BusinessHourUpdateResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        business_hour = await async_client.workers.business_hours.update(
            id="id",
            hours={"foo": "string"},
            primary_tag="primaryTag",
            secondary_tag="secondaryTag",
            timezone="timezone",
        )
        assert_matches_type(BusinessHourUpdateResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.business_hours.with_raw_response.update(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        business_hour = await response.parse()
        assert_matches_type(BusinessHourUpdateResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.business_hours.with_streaming_response.update(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            business_hour = await response.parse()
            assert_matches_type(BusinessHourUpdateResponse, business_hour, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.workers.business_hours.with_raw_response.update(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncBrainbaseLabs) -> None:
        business_hour = await async_client.workers.business_hours.list()
        assert_matches_type(BusinessHourListResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        business_hour = await async_client.workers.business_hours.list(
            include_team_phone_hours=True,
        )
        assert_matches_type(BusinessHourListResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.business_hours.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        business_hour = await response.parse()
        assert_matches_type(BusinessHourListResponse, business_hour, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.business_hours.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            business_hour = await response.parse()
            assert_matches_type(BusinessHourListResponse, business_hour, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        business_hour = await async_client.workers.business_hours.delete(
            "id",
        )
        assert business_hour is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.business_hours.with_raw_response.delete(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        business_hour = await response.parse()
        assert business_hour is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.business_hours.with_streaming_response.delete(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            business_hour = await response.parse()
            assert business_hour is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.workers.business_hours.with_raw_response.delete(
                "",
            )

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from brainbase_labs import BrainbaseLabs, AsyncBrainbaseLabs
from brainbase_labs.types.team import (
    AssetListPhoneNumbersResponse,
    AssetRegisterPhoneNumberResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAssets:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete_phone_number(self, client: BrainbaseLabs) -> None:
        asset = client.team.assets.delete_phone_number(
            "phoneNumberId",
        )
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete_phone_number(self, client: BrainbaseLabs) -> None:
        response = client.team.assets.with_raw_response.delete_phone_number(
            "phoneNumberId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        asset = response.parse()
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete_phone_number(self, client: BrainbaseLabs) -> None:
        with client.team.assets.with_streaming_response.delete_phone_number(
            "phoneNumberId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            asset = response.parse()
            assert asset is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete_phone_number(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `phone_number_id` but received ''"):
            client.team.assets.with_raw_response.delete_phone_number(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_available_phone_numbers(self, client: BrainbaseLabs) -> None:
        asset = client.team.assets.list_available_phone_numbers(
            country_code="countryCode",
            number_type="Local",
        )
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_available_phone_numbers_with_all_params(self, client: BrainbaseLabs) -> None:
        asset = client.team.assets.list_available_phone_numbers(
            country_code="countryCode",
            number_type="Local",
            area_code="areaCode",
            contains="contains",
            mms_enabled=True,
            sms_enabled=True,
            voice_enabled=True,
        )
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_available_phone_numbers(self, client: BrainbaseLabs) -> None:
        response = client.team.assets.with_raw_response.list_available_phone_numbers(
            country_code="countryCode",
            number_type="Local",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        asset = response.parse()
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_available_phone_numbers(self, client: BrainbaseLabs) -> None:
        with client.team.assets.with_streaming_response.list_available_phone_numbers(
            country_code="countryCode",
            number_type="Local",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            asset = response.parse()
            assert asset is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_phone_numbers(self, client: BrainbaseLabs) -> None:
        asset = client.team.assets.list_phone_numbers()
        assert_matches_type(AssetListPhoneNumbersResponse, asset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_phone_numbers_with_all_params(self, client: BrainbaseLabs) -> None:
        asset = client.team.assets.list_phone_numbers(
            integration_id="integrationId",
        )
        assert_matches_type(AssetListPhoneNumbersResponse, asset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_phone_numbers(self, client: BrainbaseLabs) -> None:
        response = client.team.assets.with_raw_response.list_phone_numbers()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        asset = response.parse()
        assert_matches_type(AssetListPhoneNumbersResponse, asset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_phone_numbers(self, client: BrainbaseLabs) -> None:
        with client.team.assets.with_streaming_response.list_phone_numbers() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            asset = response.parse()
            assert_matches_type(AssetListPhoneNumbersResponse, asset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_purchase_phone_numbers(self, client: BrainbaseLabs) -> None:
        asset = client.team.assets.purchase_phone_numbers(
            phone_numbers=["string"],
        )
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_purchase_phone_numbers(self, client: BrainbaseLabs) -> None:
        response = client.team.assets.with_raw_response.purchase_phone_numbers(
            phone_numbers=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        asset = response.parse()
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_purchase_phone_numbers(self, client: BrainbaseLabs) -> None:
        with client.team.assets.with_streaming_response.purchase_phone_numbers(
            phone_numbers=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            asset = response.parse()
            assert asset is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_purchase_whatsapp_sender(self, client: BrainbaseLabs) -> None:
        asset = client.team.assets.purchase_whatsapp_sender(
            phone_number="phoneNumber",
            profile={"name": "name"},
        )
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_purchase_whatsapp_sender_with_all_params(self, client: BrainbaseLabs) -> None:
        asset = client.team.assets.purchase_whatsapp_sender(
            phone_number="phoneNumber",
            profile={
                "name": "name",
                "about": "about",
                "address": "address",
                "description": "description",
                "emails": ["string"],
                "logo_url": "logoUrl",
                "vertical": "vertical",
                "websites": ["string"],
            },
        )
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_purchase_whatsapp_sender(self, client: BrainbaseLabs) -> None:
        response = client.team.assets.with_raw_response.purchase_whatsapp_sender(
            phone_number="phoneNumber",
            profile={"name": "name"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        asset = response.parse()
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_purchase_whatsapp_sender(self, client: BrainbaseLabs) -> None:
        with client.team.assets.with_streaming_response.purchase_whatsapp_sender(
            phone_number="phoneNumber",
            profile={"name": "name"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            asset = response.parse()
            assert asset is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_register_phone_number(self, client: BrainbaseLabs) -> None:
        asset = client.team.assets.register_phone_number(
            integration_id="integrationId",
            phone_number="phoneNumber",
        )
        assert_matches_type(AssetRegisterPhoneNumberResponse, asset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_register_phone_number(self, client: BrainbaseLabs) -> None:
        response = client.team.assets.with_raw_response.register_phone_number(
            integration_id="integrationId",
            phone_number="phoneNumber",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        asset = response.parse()
        assert_matches_type(AssetRegisterPhoneNumberResponse, asset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_register_phone_number(self, client: BrainbaseLabs) -> None:
        with client.team.assets.with_streaming_response.register_phone_number(
            integration_id="integrationId",
            phone_number="phoneNumber",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            asset = response.parse()
            assert_matches_type(AssetRegisterPhoneNumberResponse, asset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_whatsapp_sender_status(self, client: BrainbaseLabs) -> None:
        asset = client.team.assets.retrieve_whatsapp_sender_status(
            "senderSid",
        )
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_whatsapp_sender_status(self, client: BrainbaseLabs) -> None:
        response = client.team.assets.with_raw_response.retrieve_whatsapp_sender_status(
            "senderSid",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        asset = response.parse()
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_whatsapp_sender_status(self, client: BrainbaseLabs) -> None:
        with client.team.assets.with_streaming_response.retrieve_whatsapp_sender_status(
            "senderSid",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            asset = response.parse()
            assert asset is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_whatsapp_sender_status(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `sender_sid` but received ''"):
            client.team.assets.with_raw_response.retrieve_whatsapp_sender_status(
                "",
            )


class TestAsyncAssets:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete_phone_number(self, async_client: AsyncBrainbaseLabs) -> None:
        asset = await async_client.team.assets.delete_phone_number(
            "phoneNumberId",
        )
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete_phone_number(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.team.assets.with_raw_response.delete_phone_number(
            "phoneNumberId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        asset = await response.parse()
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete_phone_number(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.team.assets.with_streaming_response.delete_phone_number(
            "phoneNumberId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            asset = await response.parse()
            assert asset is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete_phone_number(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `phone_number_id` but received ''"):
            await async_client.team.assets.with_raw_response.delete_phone_number(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_available_phone_numbers(self, async_client: AsyncBrainbaseLabs) -> None:
        asset = await async_client.team.assets.list_available_phone_numbers(
            country_code="countryCode",
            number_type="Local",
        )
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_available_phone_numbers_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        asset = await async_client.team.assets.list_available_phone_numbers(
            country_code="countryCode",
            number_type="Local",
            area_code="areaCode",
            contains="contains",
            mms_enabled=True,
            sms_enabled=True,
            voice_enabled=True,
        )
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_available_phone_numbers(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.team.assets.with_raw_response.list_available_phone_numbers(
            country_code="countryCode",
            number_type="Local",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        asset = await response.parse()
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_available_phone_numbers(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.team.assets.with_streaming_response.list_available_phone_numbers(
            country_code="countryCode",
            number_type="Local",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            asset = await response.parse()
            assert asset is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_phone_numbers(self, async_client: AsyncBrainbaseLabs) -> None:
        asset = await async_client.team.assets.list_phone_numbers()
        assert_matches_type(AssetListPhoneNumbersResponse, asset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_phone_numbers_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        asset = await async_client.team.assets.list_phone_numbers(
            integration_id="integrationId",
        )
        assert_matches_type(AssetListPhoneNumbersResponse, asset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_phone_numbers(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.team.assets.with_raw_response.list_phone_numbers()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        asset = await response.parse()
        assert_matches_type(AssetListPhoneNumbersResponse, asset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_phone_numbers(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.team.assets.with_streaming_response.list_phone_numbers() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            asset = await response.parse()
            assert_matches_type(AssetListPhoneNumbersResponse, asset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_purchase_phone_numbers(self, async_client: AsyncBrainbaseLabs) -> None:
        asset = await async_client.team.assets.purchase_phone_numbers(
            phone_numbers=["string"],
        )
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_purchase_phone_numbers(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.team.assets.with_raw_response.purchase_phone_numbers(
            phone_numbers=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        asset = await response.parse()
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_purchase_phone_numbers(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.team.assets.with_streaming_response.purchase_phone_numbers(
            phone_numbers=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            asset = await response.parse()
            assert asset is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_purchase_whatsapp_sender(self, async_client: AsyncBrainbaseLabs) -> None:
        asset = await async_client.team.assets.purchase_whatsapp_sender(
            phone_number="phoneNumber",
            profile={"name": "name"},
        )
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_purchase_whatsapp_sender_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        asset = await async_client.team.assets.purchase_whatsapp_sender(
            phone_number="phoneNumber",
            profile={
                "name": "name",
                "about": "about",
                "address": "address",
                "description": "description",
                "emails": ["string"],
                "logo_url": "logoUrl",
                "vertical": "vertical",
                "websites": ["string"],
            },
        )
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_purchase_whatsapp_sender(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.team.assets.with_raw_response.purchase_whatsapp_sender(
            phone_number="phoneNumber",
            profile={"name": "name"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        asset = await response.parse()
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_purchase_whatsapp_sender(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.team.assets.with_streaming_response.purchase_whatsapp_sender(
            phone_number="phoneNumber",
            profile={"name": "name"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            asset = await response.parse()
            assert asset is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_register_phone_number(self, async_client: AsyncBrainbaseLabs) -> None:
        asset = await async_client.team.assets.register_phone_number(
            integration_id="integrationId",
            phone_number="phoneNumber",
        )
        assert_matches_type(AssetRegisterPhoneNumberResponse, asset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_register_phone_number(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.team.assets.with_raw_response.register_phone_number(
            integration_id="integrationId",
            phone_number="phoneNumber",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        asset = await response.parse()
        assert_matches_type(AssetRegisterPhoneNumberResponse, asset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_register_phone_number(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.team.assets.with_streaming_response.register_phone_number(
            integration_id="integrationId",
            phone_number="phoneNumber",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            asset = await response.parse()
            assert_matches_type(AssetRegisterPhoneNumberResponse, asset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_whatsapp_sender_status(self, async_client: AsyncBrainbaseLabs) -> None:
        asset = await async_client.team.assets.retrieve_whatsapp_sender_status(
            "senderSid",
        )
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_whatsapp_sender_status(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.team.assets.with_raw_response.retrieve_whatsapp_sender_status(
            "senderSid",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        asset = await response.parse()
        assert asset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_whatsapp_sender_status(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.team.assets.with_streaming_response.retrieve_whatsapp_sender_status(
            "senderSid",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            asset = await response.parse()
            assert asset is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_whatsapp_sender_status(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `sender_sid` but received ''"):
            await async_client.team.assets.with_raw_response.retrieve_whatsapp_sender_status(
                "",
            )

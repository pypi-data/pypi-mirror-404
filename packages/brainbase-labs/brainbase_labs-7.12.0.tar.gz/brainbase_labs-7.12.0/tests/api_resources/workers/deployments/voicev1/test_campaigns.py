# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from brainbase_labs import BrainbaseLabs, AsyncBrainbaseLabs
from brainbase_labs.types.workers.deployments.voicev1 import (
    CampaignCreateResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCampaigns:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: BrainbaseLabs) -> None:
        campaign = client.workers.deployments.voicev1.campaigns.create(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert_matches_type(CampaignCreateResponse, campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: BrainbaseLabs) -> None:
        campaign = client.workers.deployments.voicev1.campaigns.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            steps=[{}],
        )
        assert_matches_type(CampaignCreateResponse, campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voicev1.campaigns.with_raw_response.create(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        campaign = response.parse()
        assert_matches_type(CampaignCreateResponse, campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voicev1.campaigns.with_streaming_response.create(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            campaign = response.parse()
            assert_matches_type(CampaignCreateResponse, campaign, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voicev1.campaigns.with_raw_response.create(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voicev1.campaigns.with_raw_response.create(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: BrainbaseLabs) -> None:
        campaign = client.workers.deployments.voicev1.campaigns.retrieve(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )
        assert campaign is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voicev1.campaigns.with_raw_response.retrieve(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        campaign = response.parse()
        assert campaign is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voicev1.campaigns.with_streaming_response.retrieve(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            campaign = response.parse()
            assert campaign is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voicev1.campaigns.with_raw_response.retrieve(
                campaign_id="campaignId",
                worker_id="",
                deployment_id="deploymentId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voicev1.campaigns.with_raw_response.retrieve(
                campaign_id="campaignId",
                worker_id="workerId",
                deployment_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `campaign_id` but received ''"):
            client.workers.deployments.voicev1.campaigns.with_raw_response.retrieve(
                campaign_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_run(self, client: BrainbaseLabs) -> None:
        campaign = client.workers.deployments.voicev1.campaigns.run(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
            data=[
                {
                    "id": "id",
                    "phone_number": "phoneNumber",
                }
            ],
        )
        assert campaign is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_run(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voicev1.campaigns.with_raw_response.run(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
            data=[
                {
                    "id": "id",
                    "phone_number": "phoneNumber",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        campaign = response.parse()
        assert campaign is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_run(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voicev1.campaigns.with_streaming_response.run(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
            data=[
                {
                    "id": "id",
                    "phone_number": "phoneNumber",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            campaign = response.parse()
            assert campaign is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_run(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voicev1.campaigns.with_raw_response.run(
                campaign_id="campaignId",
                worker_id="",
                deployment_id="deploymentId",
                data=[
                    {
                        "id": "id",
                        "phone_number": "phoneNumber",
                    }
                ],
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voicev1.campaigns.with_raw_response.run(
                campaign_id="campaignId",
                worker_id="workerId",
                deployment_id="",
                data=[
                    {
                        "id": "id",
                        "phone_number": "phoneNumber",
                    }
                ],
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `campaign_id` but received ''"):
            client.workers.deployments.voicev1.campaigns.with_raw_response.run(
                campaign_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
                data=[
                    {
                        "id": "id",
                        "phone_number": "phoneNumber",
                    }
                ],
            )


class TestAsyncCampaigns:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncBrainbaseLabs) -> None:
        campaign = await async_client.workers.deployments.voicev1.campaigns.create(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert_matches_type(CampaignCreateResponse, campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        campaign = await async_client.workers.deployments.voicev1.campaigns.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            steps=[{}],
        )
        assert_matches_type(CampaignCreateResponse, campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voicev1.campaigns.with_raw_response.create(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        campaign = await response.parse()
        assert_matches_type(CampaignCreateResponse, campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voicev1.campaigns.with_streaming_response.create(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            campaign = await response.parse()
            assert_matches_type(CampaignCreateResponse, campaign, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voicev1.campaigns.with_raw_response.create(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voicev1.campaigns.with_raw_response.create(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        campaign = await async_client.workers.deployments.voicev1.campaigns.retrieve(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )
        assert campaign is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voicev1.campaigns.with_raw_response.retrieve(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        campaign = await response.parse()
        assert campaign is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voicev1.campaigns.with_streaming_response.retrieve(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            campaign = await response.parse()
            assert campaign is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voicev1.campaigns.with_raw_response.retrieve(
                campaign_id="campaignId",
                worker_id="",
                deployment_id="deploymentId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voicev1.campaigns.with_raw_response.retrieve(
                campaign_id="campaignId",
                worker_id="workerId",
                deployment_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `campaign_id` but received ''"):
            await async_client.workers.deployments.voicev1.campaigns.with_raw_response.retrieve(
                campaign_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_run(self, async_client: AsyncBrainbaseLabs) -> None:
        campaign = await async_client.workers.deployments.voicev1.campaigns.run(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
            data=[
                {
                    "id": "id",
                    "phone_number": "phoneNumber",
                }
            ],
        )
        assert campaign is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_run(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voicev1.campaigns.with_raw_response.run(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
            data=[
                {
                    "id": "id",
                    "phone_number": "phoneNumber",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        campaign = await response.parse()
        assert campaign is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_run(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voicev1.campaigns.with_streaming_response.run(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
            data=[
                {
                    "id": "id",
                    "phone_number": "phoneNumber",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            campaign = await response.parse()
            assert campaign is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_run(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voicev1.campaigns.with_raw_response.run(
                campaign_id="campaignId",
                worker_id="",
                deployment_id="deploymentId",
                data=[
                    {
                        "id": "id",
                        "phone_number": "phoneNumber",
                    }
                ],
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voicev1.campaigns.with_raw_response.run(
                campaign_id="campaignId",
                worker_id="workerId",
                deployment_id="",
                data=[
                    {
                        "id": "id",
                        "phone_number": "phoneNumber",
                    }
                ],
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `campaign_id` but received ''"):
            await async_client.workers.deployments.voicev1.campaigns.with_raw_response.run(
                campaign_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
                data=[
                    {
                        "id": "id",
                        "phone_number": "phoneNumber",
                    }
                ],
            )

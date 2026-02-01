# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from brainbase_labs import BrainbaseLabs, AsyncBrainbaseLabs
from brainbase_labs.types.workers.deployments.voice import (
    OutboundCampaignListResponse,
    OutboundCampaignCreateResponse,
    OutboundCampaignUpdateResponse,
    OutboundCampaignRetrieveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestOutboundCampaigns:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: BrainbaseLabs) -> None:
        outbound_campaign = client.workers.deployments.voice.outbound_campaigns.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[{}],
        )
        assert_matches_type(OutboundCampaignCreateResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: BrainbaseLabs) -> None:
        outbound_campaign = client.workers.deployments.voice.outbound_campaigns.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[{}],
            additional_data={},
            batch_interval_minutes=0,
            batch_size=0,
            created_by="created_by",
            description="description",
            flow_id="flow_id",
            name="name",
            status="CREATED",
            team_id="team_id",
            telephony_provider={},
        )
        assert_matches_type(OutboundCampaignCreateResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.outbound_campaigns.with_raw_response.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[{}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        outbound_campaign = response.parse()
        assert_matches_type(OutboundCampaignCreateResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.outbound_campaigns.with_streaming_response.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[{}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            outbound_campaign = response.parse()
            assert_matches_type(OutboundCampaignCreateResponse, outbound_campaign, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.outbound_campaigns.with_raw_response.create(
                deployment_id="deploymentId",
                worker_id="",
                data=[{}],
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voice.outbound_campaigns.with_raw_response.create(
                deployment_id="",
                worker_id="workerId",
                data=[{}],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: BrainbaseLabs) -> None:
        outbound_campaign = client.workers.deployments.voice.outbound_campaigns.retrieve(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )
        assert_matches_type(OutboundCampaignRetrieveResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.outbound_campaigns.with_raw_response.retrieve(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        outbound_campaign = response.parse()
        assert_matches_type(OutboundCampaignRetrieveResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.outbound_campaigns.with_streaming_response.retrieve(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            outbound_campaign = response.parse()
            assert_matches_type(OutboundCampaignRetrieveResponse, outbound_campaign, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.outbound_campaigns.with_raw_response.retrieve(
                campaign_id="campaignId",
                worker_id="",
                deployment_id="deploymentId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voice.outbound_campaigns.with_raw_response.retrieve(
                campaign_id="campaignId",
                worker_id="workerId",
                deployment_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `campaign_id` but received ''"):
            client.workers.deployments.voice.outbound_campaigns.with_raw_response.retrieve(
                campaign_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: BrainbaseLabs) -> None:
        outbound_campaign = client.workers.deployments.voice.outbound_campaigns.update(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )
        assert_matches_type(OutboundCampaignUpdateResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: BrainbaseLabs) -> None:
        outbound_campaign = client.workers.deployments.voice.outbound_campaigns.update(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
            additional_data={},
            batch_interval_minutes=0,
            batch_size=0,
            data=[{}],
            description="description",
            name="name",
            status="CREATED",
            telephony_provider={},
        )
        assert_matches_type(OutboundCampaignUpdateResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.outbound_campaigns.with_raw_response.update(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        outbound_campaign = response.parse()
        assert_matches_type(OutboundCampaignUpdateResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.outbound_campaigns.with_streaming_response.update(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            outbound_campaign = response.parse()
            assert_matches_type(OutboundCampaignUpdateResponse, outbound_campaign, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.outbound_campaigns.with_raw_response.update(
                campaign_id="campaignId",
                worker_id="",
                deployment_id="deploymentId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voice.outbound_campaigns.with_raw_response.update(
                campaign_id="campaignId",
                worker_id="workerId",
                deployment_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `campaign_id` but received ''"):
            client.workers.deployments.voice.outbound_campaigns.with_raw_response.update(
                campaign_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: BrainbaseLabs) -> None:
        outbound_campaign = client.workers.deployments.voice.outbound_campaigns.list(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert_matches_type(OutboundCampaignListResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.outbound_campaigns.with_raw_response.list(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        outbound_campaign = response.parse()
        assert_matches_type(OutboundCampaignListResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.outbound_campaigns.with_streaming_response.list(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            outbound_campaign = response.parse()
            assert_matches_type(OutboundCampaignListResponse, outbound_campaign, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.outbound_campaigns.with_raw_response.list(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voice.outbound_campaigns.with_raw_response.list(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: BrainbaseLabs) -> None:
        outbound_campaign = client.workers.deployments.voice.outbound_campaigns.delete(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )
        assert outbound_campaign is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.outbound_campaigns.with_raw_response.delete(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        outbound_campaign = response.parse()
        assert outbound_campaign is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.outbound_campaigns.with_streaming_response.delete(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            outbound_campaign = response.parse()
            assert outbound_campaign is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.outbound_campaigns.with_raw_response.delete(
                campaign_id="campaignId",
                worker_id="",
                deployment_id="deploymentId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voice.outbound_campaigns.with_raw_response.delete(
                campaign_id="campaignId",
                worker_id="workerId",
                deployment_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `campaign_id` but received ''"):
            client.workers.deployments.voice.outbound_campaigns.with_raw_response.delete(
                campaign_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
            )


class TestAsyncOutboundCampaigns:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncBrainbaseLabs) -> None:
        outbound_campaign = await async_client.workers.deployments.voice.outbound_campaigns.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[{}],
        )
        assert_matches_type(OutboundCampaignCreateResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        outbound_campaign = await async_client.workers.deployments.voice.outbound_campaigns.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[{}],
            additional_data={},
            batch_interval_minutes=0,
            batch_size=0,
            created_by="created_by",
            description="description",
            flow_id="flow_id",
            name="name",
            status="CREATED",
            team_id="team_id",
            telephony_provider={},
        )
        assert_matches_type(OutboundCampaignCreateResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[{}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        outbound_campaign = await response.parse()
        assert_matches_type(OutboundCampaignCreateResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.outbound_campaigns.with_streaming_response.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[{}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            outbound_campaign = await response.parse()
            assert_matches_type(OutboundCampaignCreateResponse, outbound_campaign, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.create(
                deployment_id="deploymentId",
                worker_id="",
                data=[{}],
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.create(
                deployment_id="",
                worker_id="workerId",
                data=[{}],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        outbound_campaign = await async_client.workers.deployments.voice.outbound_campaigns.retrieve(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )
        assert_matches_type(OutboundCampaignRetrieveResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.retrieve(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        outbound_campaign = await response.parse()
        assert_matches_type(OutboundCampaignRetrieveResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.outbound_campaigns.with_streaming_response.retrieve(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            outbound_campaign = await response.parse()
            assert_matches_type(OutboundCampaignRetrieveResponse, outbound_campaign, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.retrieve(
                campaign_id="campaignId",
                worker_id="",
                deployment_id="deploymentId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.retrieve(
                campaign_id="campaignId",
                worker_id="workerId",
                deployment_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `campaign_id` but received ''"):
            await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.retrieve(
                campaign_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncBrainbaseLabs) -> None:
        outbound_campaign = await async_client.workers.deployments.voice.outbound_campaigns.update(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )
        assert_matches_type(OutboundCampaignUpdateResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        outbound_campaign = await async_client.workers.deployments.voice.outbound_campaigns.update(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
            additional_data={},
            batch_interval_minutes=0,
            batch_size=0,
            data=[{}],
            description="description",
            name="name",
            status="CREATED",
            telephony_provider={},
        )
        assert_matches_type(OutboundCampaignUpdateResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.update(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        outbound_campaign = await response.parse()
        assert_matches_type(OutboundCampaignUpdateResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.outbound_campaigns.with_streaming_response.update(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            outbound_campaign = await response.parse()
            assert_matches_type(OutboundCampaignUpdateResponse, outbound_campaign, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.update(
                campaign_id="campaignId",
                worker_id="",
                deployment_id="deploymentId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.update(
                campaign_id="campaignId",
                worker_id="workerId",
                deployment_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `campaign_id` but received ''"):
            await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.update(
                campaign_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncBrainbaseLabs) -> None:
        outbound_campaign = await async_client.workers.deployments.voice.outbound_campaigns.list(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert_matches_type(OutboundCampaignListResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.list(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        outbound_campaign = await response.parse()
        assert_matches_type(OutboundCampaignListResponse, outbound_campaign, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.outbound_campaigns.with_streaming_response.list(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            outbound_campaign = await response.parse()
            assert_matches_type(OutboundCampaignListResponse, outbound_campaign, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.list(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.list(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        outbound_campaign = await async_client.workers.deployments.voice.outbound_campaigns.delete(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )
        assert outbound_campaign is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.delete(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        outbound_campaign = await response.parse()
        assert outbound_campaign is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.outbound_campaigns.with_streaming_response.delete(
            campaign_id="campaignId",
            worker_id="workerId",
            deployment_id="deploymentId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            outbound_campaign = await response.parse()
            assert outbound_campaign is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.delete(
                campaign_id="campaignId",
                worker_id="",
                deployment_id="deploymentId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.delete(
                campaign_id="campaignId",
                worker_id="workerId",
                deployment_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `campaign_id` but received ''"):
            await async_client.workers.deployments.voice.outbound_campaigns.with_raw_response.delete(
                campaign_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
            )

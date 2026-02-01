# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from brainbase_labs import BrainbaseLabs, AsyncBrainbaseLabs

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestData:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: BrainbaseLabs) -> None:
        data = client.workers.deployments.voicev1.campaigns.data.retrieve(
            data_id="dataId",
            worker_id="workerId",
            deployment_id="deploymentId",
            campaign_id="campaignId",
        )
        assert data is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voicev1.campaigns.data.with_raw_response.retrieve(
            data_id="dataId",
            worker_id="workerId",
            deployment_id="deploymentId",
            campaign_id="campaignId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        data = response.parse()
        assert data is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voicev1.campaigns.data.with_streaming_response.retrieve(
            data_id="dataId",
            worker_id="workerId",
            deployment_id="deploymentId",
            campaign_id="campaignId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            data = response.parse()
            assert data is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voicev1.campaigns.data.with_raw_response.retrieve(
                data_id="dataId",
                worker_id="",
                deployment_id="deploymentId",
                campaign_id="campaignId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voicev1.campaigns.data.with_raw_response.retrieve(
                data_id="dataId",
                worker_id="workerId",
                deployment_id="",
                campaign_id="campaignId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `campaign_id` but received ''"):
            client.workers.deployments.voicev1.campaigns.data.with_raw_response.retrieve(
                data_id="dataId",
                worker_id="workerId",
                deployment_id="deploymentId",
                campaign_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `data_id` but received ''"):
            client.workers.deployments.voicev1.campaigns.data.with_raw_response.retrieve(
                data_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
                campaign_id="campaignId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: BrainbaseLabs) -> None:
        data = client.workers.deployments.voicev1.campaigns.data.update(
            data_id="dataId",
            worker_id="workerId",
            deployment_id="deploymentId",
            campaign_id="campaignId",
        )
        assert data is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: BrainbaseLabs) -> None:
        data = client.workers.deployments.voicev1.campaigns.data.update(
            data_id="dataId",
            worker_id="workerId",
            deployment_id="deploymentId",
            campaign_id="campaignId",
            result={},
            row_data={},
            status="PENDING",
        )
        assert data is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voicev1.campaigns.data.with_raw_response.update(
            data_id="dataId",
            worker_id="workerId",
            deployment_id="deploymentId",
            campaign_id="campaignId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        data = response.parse()
        assert data is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voicev1.campaigns.data.with_streaming_response.update(
            data_id="dataId",
            worker_id="workerId",
            deployment_id="deploymentId",
            campaign_id="campaignId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            data = response.parse()
            assert data is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voicev1.campaigns.data.with_raw_response.update(
                data_id="dataId",
                worker_id="",
                deployment_id="deploymentId",
                campaign_id="campaignId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voicev1.campaigns.data.with_raw_response.update(
                data_id="dataId",
                worker_id="workerId",
                deployment_id="",
                campaign_id="campaignId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `campaign_id` but received ''"):
            client.workers.deployments.voicev1.campaigns.data.with_raw_response.update(
                data_id="dataId",
                worker_id="workerId",
                deployment_id="deploymentId",
                campaign_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `data_id` but received ''"):
            client.workers.deployments.voicev1.campaigns.data.with_raw_response.update(
                data_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
                campaign_id="campaignId",
            )


class TestAsyncData:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        data = await async_client.workers.deployments.voicev1.campaigns.data.retrieve(
            data_id="dataId",
            worker_id="workerId",
            deployment_id="deploymentId",
            campaign_id="campaignId",
        )
        assert data is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voicev1.campaigns.data.with_raw_response.retrieve(
            data_id="dataId",
            worker_id="workerId",
            deployment_id="deploymentId",
            campaign_id="campaignId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        data = await response.parse()
        assert data is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voicev1.campaigns.data.with_streaming_response.retrieve(
            data_id="dataId",
            worker_id="workerId",
            deployment_id="deploymentId",
            campaign_id="campaignId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            data = await response.parse()
            assert data is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voicev1.campaigns.data.with_raw_response.retrieve(
                data_id="dataId",
                worker_id="",
                deployment_id="deploymentId",
                campaign_id="campaignId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voicev1.campaigns.data.with_raw_response.retrieve(
                data_id="dataId",
                worker_id="workerId",
                deployment_id="",
                campaign_id="campaignId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `campaign_id` but received ''"):
            await async_client.workers.deployments.voicev1.campaigns.data.with_raw_response.retrieve(
                data_id="dataId",
                worker_id="workerId",
                deployment_id="deploymentId",
                campaign_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `data_id` but received ''"):
            await async_client.workers.deployments.voicev1.campaigns.data.with_raw_response.retrieve(
                data_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
                campaign_id="campaignId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncBrainbaseLabs) -> None:
        data = await async_client.workers.deployments.voicev1.campaigns.data.update(
            data_id="dataId",
            worker_id="workerId",
            deployment_id="deploymentId",
            campaign_id="campaignId",
        )
        assert data is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        data = await async_client.workers.deployments.voicev1.campaigns.data.update(
            data_id="dataId",
            worker_id="workerId",
            deployment_id="deploymentId",
            campaign_id="campaignId",
            result={},
            row_data={},
            status="PENDING",
        )
        assert data is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voicev1.campaigns.data.with_raw_response.update(
            data_id="dataId",
            worker_id="workerId",
            deployment_id="deploymentId",
            campaign_id="campaignId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        data = await response.parse()
        assert data is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voicev1.campaigns.data.with_streaming_response.update(
            data_id="dataId",
            worker_id="workerId",
            deployment_id="deploymentId",
            campaign_id="campaignId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            data = await response.parse()
            assert data is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voicev1.campaigns.data.with_raw_response.update(
                data_id="dataId",
                worker_id="",
                deployment_id="deploymentId",
                campaign_id="campaignId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voicev1.campaigns.data.with_raw_response.update(
                data_id="dataId",
                worker_id="workerId",
                deployment_id="",
                campaign_id="campaignId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `campaign_id` but received ''"):
            await async_client.workers.deployments.voicev1.campaigns.data.with_raw_response.update(
                data_id="dataId",
                worker_id="workerId",
                deployment_id="deploymentId",
                campaign_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `data_id` but received ''"):
            await async_client.workers.deployments.voicev1.campaigns.data.with_raw_response.update(
                data_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
                campaign_id="campaignId",
            )

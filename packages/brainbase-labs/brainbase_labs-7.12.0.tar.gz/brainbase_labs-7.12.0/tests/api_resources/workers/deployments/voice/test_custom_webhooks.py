# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from brainbase_labs import BrainbaseLabs, AsyncBrainbaseLabs

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCustomWebhooks:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: BrainbaseLabs) -> None:
        custom_webhook = client.workers.deployments.voice.custom_webhooks.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            fields="fields",
            url="url",
        )
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: BrainbaseLabs) -> None:
        custom_webhook = client.workers.deployments.voice.custom_webhooks.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            fields="fields",
            url="url",
            active=True,
            method="GET",
            name="name",
        )
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.custom_webhooks.with_raw_response.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            fields="fields",
            url="url",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        custom_webhook = response.parse()
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.custom_webhooks.with_streaming_response.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            fields="fields",
            url="url",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            custom_webhook = response.parse()
            assert custom_webhook is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.custom_webhooks.with_raw_response.create(
                deployment_id="deploymentId",
                worker_id="",
                fields="fields",
                url="url",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voice.custom_webhooks.with_raw_response.create(
                deployment_id="",
                worker_id="workerId",
                fields="fields",
                url="url",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: BrainbaseLabs) -> None:
        custom_webhook = client.workers.deployments.voice.custom_webhooks.retrieve(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.custom_webhooks.with_raw_response.retrieve(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        custom_webhook = response.parse()
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.custom_webhooks.with_streaming_response.retrieve(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            custom_webhook = response.parse()
            assert custom_webhook is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.custom_webhooks.with_raw_response.retrieve(
                webhook_id="webhookId",
                worker_id="",
                deployment_id="deploymentId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voice.custom_webhooks.with_raw_response.retrieve(
                webhook_id="webhookId",
                worker_id="workerId",
                deployment_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `webhook_id` but received ''"):
            client.workers.deployments.voice.custom_webhooks.with_raw_response.retrieve(
                webhook_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: BrainbaseLabs) -> None:
        custom_webhook = client.workers.deployments.voice.custom_webhooks.update(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: BrainbaseLabs) -> None:
        custom_webhook = client.workers.deployments.voice.custom_webhooks.update(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
            active=True,
            fields="fields",
            method="GET",
            name="name",
            url="url",
        )
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.custom_webhooks.with_raw_response.update(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        custom_webhook = response.parse()
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.custom_webhooks.with_streaming_response.update(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            custom_webhook = response.parse()
            assert custom_webhook is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.custom_webhooks.with_raw_response.update(
                webhook_id="webhookId",
                worker_id="",
                deployment_id="deploymentId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voice.custom_webhooks.with_raw_response.update(
                webhook_id="webhookId",
                worker_id="workerId",
                deployment_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `webhook_id` but received ''"):
            client.workers.deployments.voice.custom_webhooks.with_raw_response.update(
                webhook_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: BrainbaseLabs) -> None:
        custom_webhook = client.workers.deployments.voice.custom_webhooks.list(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.custom_webhooks.with_raw_response.list(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        custom_webhook = response.parse()
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.custom_webhooks.with_streaming_response.list(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            custom_webhook = response.parse()
            assert custom_webhook is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.custom_webhooks.with_raw_response.list(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voice.custom_webhooks.with_raw_response.list(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: BrainbaseLabs) -> None:
        custom_webhook = client.workers.deployments.voice.custom_webhooks.delete(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.custom_webhooks.with_raw_response.delete(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        custom_webhook = response.parse()
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.custom_webhooks.with_streaming_response.delete(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            custom_webhook = response.parse()
            assert custom_webhook is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.custom_webhooks.with_raw_response.delete(
                webhook_id="webhookId",
                worker_id="",
                deployment_id="deploymentId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voice.custom_webhooks.with_raw_response.delete(
                webhook_id="webhookId",
                worker_id="workerId",
                deployment_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `webhook_id` but received ''"):
            client.workers.deployments.voice.custom_webhooks.with_raw_response.delete(
                webhook_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
            )


class TestAsyncCustomWebhooks:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncBrainbaseLabs) -> None:
        custom_webhook = await async_client.workers.deployments.voice.custom_webhooks.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            fields="fields",
            url="url",
        )
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        custom_webhook = await async_client.workers.deployments.voice.custom_webhooks.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            fields="fields",
            url="url",
            active=True,
            method="GET",
            name="name",
        )
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            fields="fields",
            url="url",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        custom_webhook = await response.parse()
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.custom_webhooks.with_streaming_response.create(
            deployment_id="deploymentId",
            worker_id="workerId",
            fields="fields",
            url="url",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            custom_webhook = await response.parse()
            assert custom_webhook is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.create(
                deployment_id="deploymentId",
                worker_id="",
                fields="fields",
                url="url",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.create(
                deployment_id="",
                worker_id="workerId",
                fields="fields",
                url="url",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        custom_webhook = await async_client.workers.deployments.voice.custom_webhooks.retrieve(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.retrieve(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        custom_webhook = await response.parse()
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.custom_webhooks.with_streaming_response.retrieve(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            custom_webhook = await response.parse()
            assert custom_webhook is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.retrieve(
                webhook_id="webhookId",
                worker_id="",
                deployment_id="deploymentId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.retrieve(
                webhook_id="webhookId",
                worker_id="workerId",
                deployment_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `webhook_id` but received ''"):
            await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.retrieve(
                webhook_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncBrainbaseLabs) -> None:
        custom_webhook = await async_client.workers.deployments.voice.custom_webhooks.update(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        custom_webhook = await async_client.workers.deployments.voice.custom_webhooks.update(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
            active=True,
            fields="fields",
            method="GET",
            name="name",
            url="url",
        )
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.update(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        custom_webhook = await response.parse()
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.custom_webhooks.with_streaming_response.update(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            custom_webhook = await response.parse()
            assert custom_webhook is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.update(
                webhook_id="webhookId",
                worker_id="",
                deployment_id="deploymentId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.update(
                webhook_id="webhookId",
                worker_id="workerId",
                deployment_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `webhook_id` but received ''"):
            await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.update(
                webhook_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncBrainbaseLabs) -> None:
        custom_webhook = await async_client.workers.deployments.voice.custom_webhooks.list(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.list(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        custom_webhook = await response.parse()
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.custom_webhooks.with_streaming_response.list(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            custom_webhook = await response.parse()
            assert custom_webhook is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.list(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.list(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        custom_webhook = await async_client.workers.deployments.voice.custom_webhooks.delete(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.delete(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        custom_webhook = await response.parse()
        assert custom_webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.custom_webhooks.with_streaming_response.delete(
            webhook_id="webhookId",
            worker_id="workerId",
            deployment_id="deploymentId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            custom_webhook = await response.parse()
            assert custom_webhook is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.delete(
                webhook_id="webhookId",
                worker_id="",
                deployment_id="deploymentId",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.delete(
                webhook_id="webhookId",
                worker_id="workerId",
                deployment_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `webhook_id` but received ''"):
            await async_client.workers.deployments.voice.custom_webhooks.with_raw_response.delete(
                webhook_id="",
                worker_id="workerId",
                deployment_id="deploymentId",
            )

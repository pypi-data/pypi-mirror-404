# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from brainbase_labs import BrainbaseLabs, AsyncBrainbaseLabs
from brainbase_labs.types.workers import TestCreateResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTests:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: BrainbaseLabs) -> None:
        test = client.workers.tests.create(
            worker_id="workerId",
            checkpoints=[
                {
                    "description": "description",
                    "name": "name",
                    "runs": 0,
                    "tolerance": 0,
                }
            ],
            description="description",
            flow_id="flowId",
            name="name",
            system_prompt="systemPrompt",
            test_mode="testMode",
        )
        assert_matches_type(TestCreateResponse, test, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: BrainbaseLabs) -> None:
        response = client.workers.tests.with_raw_response.create(
            worker_id="workerId",
            checkpoints=[
                {
                    "description": "description",
                    "name": "name",
                    "runs": 0,
                    "tolerance": 0,
                }
            ],
            description="description",
            flow_id="flowId",
            name="name",
            system_prompt="systemPrompt",
            test_mode="testMode",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        test = response.parse()
        assert_matches_type(TestCreateResponse, test, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: BrainbaseLabs) -> None:
        with client.workers.tests.with_streaming_response.create(
            worker_id="workerId",
            checkpoints=[
                {
                    "description": "description",
                    "name": "name",
                    "runs": 0,
                    "tolerance": 0,
                }
            ],
            description="description",
            flow_id="flowId",
            name="name",
            system_prompt="systemPrompt",
            test_mode="testMode",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            test = response.parse()
            assert_matches_type(TestCreateResponse, test, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.tests.with_raw_response.create(
                worker_id="",
                checkpoints=[
                    {
                        "description": "description",
                        "name": "name",
                        "runs": 0,
                        "tolerance": 0,
                    }
                ],
                description="description",
                flow_id="flowId",
                name="name",
                system_prompt="systemPrompt",
                test_mode="testMode",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: BrainbaseLabs) -> None:
        test = client.workers.tests.update(
            test_id="testId",
            worker_id="workerId",
        )
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: BrainbaseLabs) -> None:
        test = client.workers.tests.update(
            test_id="testId",
            worker_id="workerId",
            checkpoints=[
                {
                    "description": "description",
                    "name": "name",
                    "runs": 0,
                    "tolerance": 0,
                }
            ],
            description="description",
            flow_id="flowId",
            name="name",
            system_prompt="systemPrompt",
            test_mode="testMode",
        )
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: BrainbaseLabs) -> None:
        response = client.workers.tests.with_raw_response.update(
            test_id="testId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        test = response.parse()
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: BrainbaseLabs) -> None:
        with client.workers.tests.with_streaming_response.update(
            test_id="testId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            test = response.parse()
            assert test is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.tests.with_raw_response.update(
                test_id="testId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `test_id` but received ''"):
            client.workers.tests.with_raw_response.update(
                test_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: BrainbaseLabs) -> None:
        test = client.workers.tests.delete(
            test_id="testId",
            worker_id="workerId",
        )
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: BrainbaseLabs) -> None:
        response = client.workers.tests.with_raw_response.delete(
            test_id="testId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        test = response.parse()
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: BrainbaseLabs) -> None:
        with client.workers.tests.with_streaming_response.delete(
            test_id="testId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            test = response.parse()
            assert test is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.tests.with_raw_response.delete(
                test_id="testId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `test_id` but received ''"):
            client.workers.tests.with_raw_response.delete(
                test_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_runs(self, client: BrainbaseLabs) -> None:
        test = client.workers.tests.list_runs(
            test_id="testId",
            worker_id="workerId",
        )
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_runs(self, client: BrainbaseLabs) -> None:
        response = client.workers.tests.with_raw_response.list_runs(
            test_id="testId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        test = response.parse()
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_runs(self, client: BrainbaseLabs) -> None:
        with client.workers.tests.with_streaming_response.list_runs(
            test_id="testId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            test = response.parse()
            assert test is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list_runs(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.tests.with_raw_response.list_runs(
                test_id="testId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `test_id` but received ''"):
            client.workers.tests.with_raw_response.list_runs(
                test_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_run(self, client: BrainbaseLabs) -> None:
        test = client.workers.tests.run(
            test_id="testId",
            worker_id="workerId",
        )
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_run(self, client: BrainbaseLabs) -> None:
        response = client.workers.tests.with_raw_response.run(
            test_id="testId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        test = response.parse()
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_run(self, client: BrainbaseLabs) -> None:
        with client.workers.tests.with_streaming_response.run(
            test_id="testId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            test = response.parse()
            assert test is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_run(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.tests.with_raw_response.run(
                test_id="testId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `test_id` but received ''"):
            client.workers.tests.with_raw_response.run(
                test_id="",
                worker_id="workerId",
            )


class TestAsyncTests:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncBrainbaseLabs) -> None:
        test = await async_client.workers.tests.create(
            worker_id="workerId",
            checkpoints=[
                {
                    "description": "description",
                    "name": "name",
                    "runs": 0,
                    "tolerance": 0,
                }
            ],
            description="description",
            flow_id="flowId",
            name="name",
            system_prompt="systemPrompt",
            test_mode="testMode",
        )
        assert_matches_type(TestCreateResponse, test, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.tests.with_raw_response.create(
            worker_id="workerId",
            checkpoints=[
                {
                    "description": "description",
                    "name": "name",
                    "runs": 0,
                    "tolerance": 0,
                }
            ],
            description="description",
            flow_id="flowId",
            name="name",
            system_prompt="systemPrompt",
            test_mode="testMode",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        test = await response.parse()
        assert_matches_type(TestCreateResponse, test, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.tests.with_streaming_response.create(
            worker_id="workerId",
            checkpoints=[
                {
                    "description": "description",
                    "name": "name",
                    "runs": 0,
                    "tolerance": 0,
                }
            ],
            description="description",
            flow_id="flowId",
            name="name",
            system_prompt="systemPrompt",
            test_mode="testMode",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            test = await response.parse()
            assert_matches_type(TestCreateResponse, test, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.tests.with_raw_response.create(
                worker_id="",
                checkpoints=[
                    {
                        "description": "description",
                        "name": "name",
                        "runs": 0,
                        "tolerance": 0,
                    }
                ],
                description="description",
                flow_id="flowId",
                name="name",
                system_prompt="systemPrompt",
                test_mode="testMode",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncBrainbaseLabs) -> None:
        test = await async_client.workers.tests.update(
            test_id="testId",
            worker_id="workerId",
        )
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        test = await async_client.workers.tests.update(
            test_id="testId",
            worker_id="workerId",
            checkpoints=[
                {
                    "description": "description",
                    "name": "name",
                    "runs": 0,
                    "tolerance": 0,
                }
            ],
            description="description",
            flow_id="flowId",
            name="name",
            system_prompt="systemPrompt",
            test_mode="testMode",
        )
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.tests.with_raw_response.update(
            test_id="testId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        test = await response.parse()
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.tests.with_streaming_response.update(
            test_id="testId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            test = await response.parse()
            assert test is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.tests.with_raw_response.update(
                test_id="testId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `test_id` but received ''"):
            await async_client.workers.tests.with_raw_response.update(
                test_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        test = await async_client.workers.tests.delete(
            test_id="testId",
            worker_id="workerId",
        )
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.tests.with_raw_response.delete(
            test_id="testId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        test = await response.parse()
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.tests.with_streaming_response.delete(
            test_id="testId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            test = await response.parse()
            assert test is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.tests.with_raw_response.delete(
                test_id="testId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `test_id` but received ''"):
            await async_client.workers.tests.with_raw_response.delete(
                test_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_runs(self, async_client: AsyncBrainbaseLabs) -> None:
        test = await async_client.workers.tests.list_runs(
            test_id="testId",
            worker_id="workerId",
        )
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_runs(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.tests.with_raw_response.list_runs(
            test_id="testId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        test = await response.parse()
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_runs(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.tests.with_streaming_response.list_runs(
            test_id="testId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            test = await response.parse()
            assert test is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list_runs(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.tests.with_raw_response.list_runs(
                test_id="testId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `test_id` but received ''"):
            await async_client.workers.tests.with_raw_response.list_runs(
                test_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_run(self, async_client: AsyncBrainbaseLabs) -> None:
        test = await async_client.workers.tests.run(
            test_id="testId",
            worker_id="workerId",
        )
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_run(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.tests.with_raw_response.run(
            test_id="testId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        test = await response.parse()
        assert test is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_run(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.tests.with_streaming_response.run(
            test_id="testId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            test = await response.parse()
            assert test is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_run(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.tests.with_raw_response.run(
                test_id="testId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `test_id` but received ''"):
            await async_client.workers.tests.with_raw_response.run(
                test_id="",
                worker_id="workerId",
            )

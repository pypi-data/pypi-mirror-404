# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from brainbase_labs import BrainbaseLabs, AsyncBrainbaseLabs

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRuntimeErrors:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: BrainbaseLabs) -> None:
        runtime_error = client.workers.runtime_errors.retrieve(
            error_id="errorId",
            worker_id="workerId",
        )
        assert runtime_error is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: BrainbaseLabs) -> None:
        response = client.workers.runtime_errors.with_raw_response.retrieve(
            error_id="errorId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        runtime_error = response.parse()
        assert runtime_error is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: BrainbaseLabs) -> None:
        with client.workers.runtime_errors.with_streaming_response.retrieve(
            error_id="errorId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            runtime_error = response.parse()
            assert runtime_error is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.runtime_errors.with_raw_response.retrieve(
                error_id="errorId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `error_id` but received ''"):
            client.workers.runtime_errors.with_raw_response.retrieve(
                error_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: BrainbaseLabs) -> None:
        runtime_error = client.workers.runtime_errors.list(
            worker_id="workerId",
        )
        assert runtime_error is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: BrainbaseLabs) -> None:
        runtime_error = client.workers.runtime_errors.list(
            worker_id="workerId",
            deployment_id="deploymentId",
            limit=0,
            offset=0,
            service="service",
            severity="severity",
            type="type",
        )
        assert runtime_error is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: BrainbaseLabs) -> None:
        response = client.workers.runtime_errors.with_raw_response.list(
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        runtime_error = response.parse()
        assert runtime_error is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: BrainbaseLabs) -> None:
        with client.workers.runtime_errors.with_streaming_response.list(
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            runtime_error = response.parse()
            assert runtime_error is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.runtime_errors.with_raw_response.list(
                worker_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_record(self, client: BrainbaseLabs) -> None:
        runtime_error = client.workers.runtime_errors.record(
            worker_id="workerId",
            error="error",
            service="service",
            type="type",
        )
        assert runtime_error is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_record_with_all_params(self, client: BrainbaseLabs) -> None:
        runtime_error = client.workers.runtime_errors.record(
            worker_id="workerId",
            error="error",
            service="service",
            type="type",
            bb_engine_session_id="bbEngineSessionId",
            deployment_id="deploymentId",
            flow_id="flowId",
            function_name="functionName",
            line_number=0,
            metadata={},
            severity="warning",
            traceback="traceback",
        )
        assert runtime_error is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_record(self, client: BrainbaseLabs) -> None:
        response = client.workers.runtime_errors.with_raw_response.record(
            worker_id="workerId",
            error="error",
            service="service",
            type="type",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        runtime_error = response.parse()
        assert runtime_error is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_record(self, client: BrainbaseLabs) -> None:
        with client.workers.runtime_errors.with_streaming_response.record(
            worker_id="workerId",
            error="error",
            service="service",
            type="type",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            runtime_error = response.parse()
            assert runtime_error is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_record(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.runtime_errors.with_raw_response.record(
                worker_id="",
                error="error",
                service="service",
                type="type",
            )


class TestAsyncRuntimeErrors:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        runtime_error = await async_client.workers.runtime_errors.retrieve(
            error_id="errorId",
            worker_id="workerId",
        )
        assert runtime_error is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.runtime_errors.with_raw_response.retrieve(
            error_id="errorId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        runtime_error = await response.parse()
        assert runtime_error is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.runtime_errors.with_streaming_response.retrieve(
            error_id="errorId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            runtime_error = await response.parse()
            assert runtime_error is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.runtime_errors.with_raw_response.retrieve(
                error_id="errorId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `error_id` but received ''"):
            await async_client.workers.runtime_errors.with_raw_response.retrieve(
                error_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncBrainbaseLabs) -> None:
        runtime_error = await async_client.workers.runtime_errors.list(
            worker_id="workerId",
        )
        assert runtime_error is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        runtime_error = await async_client.workers.runtime_errors.list(
            worker_id="workerId",
            deployment_id="deploymentId",
            limit=0,
            offset=0,
            service="service",
            severity="severity",
            type="type",
        )
        assert runtime_error is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.runtime_errors.with_raw_response.list(
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        runtime_error = await response.parse()
        assert runtime_error is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.runtime_errors.with_streaming_response.list(
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            runtime_error = await response.parse()
            assert runtime_error is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.runtime_errors.with_raw_response.list(
                worker_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_record(self, async_client: AsyncBrainbaseLabs) -> None:
        runtime_error = await async_client.workers.runtime_errors.record(
            worker_id="workerId",
            error="error",
            service="service",
            type="type",
        )
        assert runtime_error is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_record_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        runtime_error = await async_client.workers.runtime_errors.record(
            worker_id="workerId",
            error="error",
            service="service",
            type="type",
            bb_engine_session_id="bbEngineSessionId",
            deployment_id="deploymentId",
            flow_id="flowId",
            function_name="functionName",
            line_number=0,
            metadata={},
            severity="warning",
            traceback="traceback",
        )
        assert runtime_error is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_record(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.runtime_errors.with_raw_response.record(
            worker_id="workerId",
            error="error",
            service="service",
            type="type",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        runtime_error = await response.parse()
        assert runtime_error is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_record(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.runtime_errors.with_streaming_response.record(
            worker_id="workerId",
            error="error",
            service="service",
            type="type",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            runtime_error = await response.parse()
            assert runtime_error is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_record(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.runtime_errors.with_raw_response.record(
                worker_id="",
                error="error",
                service="service",
                type="type",
            )

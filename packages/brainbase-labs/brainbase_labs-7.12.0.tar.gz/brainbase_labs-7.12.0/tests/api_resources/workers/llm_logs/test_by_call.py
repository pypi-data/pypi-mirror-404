# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from brainbase_labs import BrainbaseLabs, AsyncBrainbaseLabs

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestByCall:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: BrainbaseLabs) -> None:
        by_call = client.workers.llm_logs.by_call.list(
            call_id="callId",
            worker_id="workerId",
        )
        assert by_call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: BrainbaseLabs) -> None:
        response = client.workers.llm_logs.by_call.with_raw_response.list(
            call_id="callId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        by_call = response.parse()
        assert by_call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: BrainbaseLabs) -> None:
        with client.workers.llm_logs.by_call.with_streaming_response.list(
            call_id="callId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            by_call = response.parse()
            assert by_call is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.llm_logs.by_call.with_raw_response.list(
                call_id="callId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `call_id` but received ''"):
            client.workers.llm_logs.by_call.with_raw_response.list(
                call_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: BrainbaseLabs) -> None:
        by_call = client.workers.llm_logs.by_call.delete(
            call_id="callId",
            worker_id="workerId",
        )
        assert by_call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: BrainbaseLabs) -> None:
        response = client.workers.llm_logs.by_call.with_raw_response.delete(
            call_id="callId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        by_call = response.parse()
        assert by_call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: BrainbaseLabs) -> None:
        with client.workers.llm_logs.by_call.with_streaming_response.delete(
            call_id="callId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            by_call = response.parse()
            assert by_call is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.llm_logs.by_call.with_raw_response.delete(
                call_id="callId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `call_id` but received ''"):
            client.workers.llm_logs.by_call.with_raw_response.delete(
                call_id="",
                worker_id="workerId",
            )


class TestAsyncByCall:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncBrainbaseLabs) -> None:
        by_call = await async_client.workers.llm_logs.by_call.list(
            call_id="callId",
            worker_id="workerId",
        )
        assert by_call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.llm_logs.by_call.with_raw_response.list(
            call_id="callId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        by_call = await response.parse()
        assert by_call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.llm_logs.by_call.with_streaming_response.list(
            call_id="callId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            by_call = await response.parse()
            assert by_call is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.llm_logs.by_call.with_raw_response.list(
                call_id="callId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `call_id` but received ''"):
            await async_client.workers.llm_logs.by_call.with_raw_response.list(
                call_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        by_call = await async_client.workers.llm_logs.by_call.delete(
            call_id="callId",
            worker_id="workerId",
        )
        assert by_call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.llm_logs.by_call.with_raw_response.delete(
            call_id="callId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        by_call = await response.parse()
        assert by_call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.llm_logs.by_call.with_streaming_response.delete(
            call_id="callId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            by_call = await response.parse()
            assert by_call is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.llm_logs.by_call.with_raw_response.delete(
                call_id="callId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `call_id` but received ''"):
            await async_client.workers.llm_logs.by_call.with_raw_response.delete(
                call_id="",
                worker_id="workerId",
            )

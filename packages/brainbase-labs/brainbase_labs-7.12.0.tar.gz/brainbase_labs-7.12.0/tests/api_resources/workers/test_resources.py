# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from brainbase_labs import BrainbaseLabs, AsyncBrainbaseLabs
from brainbase_labs.types.shared import Resource
from brainbase_labs.types.workers import ResourceQueryResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestResources:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: BrainbaseLabs) -> None:
        resource = client.workers.resources.retrieve(
            resource_id="resourceId",
            worker_id="workerId",
        )
        assert_matches_type(Resource, resource, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: BrainbaseLabs) -> None:
        response = client.workers.resources.with_raw_response.retrieve(
            resource_id="resourceId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource = response.parse()
        assert_matches_type(Resource, resource, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: BrainbaseLabs) -> None:
        with client.workers.resources.with_streaming_response.retrieve(
            resource_id="resourceId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource = response.parse()
            assert_matches_type(Resource, resource, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.resources.with_raw_response.retrieve(
                resource_id="resourceId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_id` but received ''"):
            client.workers.resources.with_raw_response.retrieve(
                resource_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: BrainbaseLabs) -> None:
        resource = client.workers.resources.delete(
            resource_id="resourceId",
            worker_id="workerId",
        )
        assert resource is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: BrainbaseLabs) -> None:
        response = client.workers.resources.with_raw_response.delete(
            resource_id="resourceId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource = response.parse()
        assert resource is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: BrainbaseLabs) -> None:
        with client.workers.resources.with_streaming_response.delete(
            resource_id="resourceId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource = response.parse()
            assert resource is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.resources.with_raw_response.delete(
                resource_id="resourceId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_id` but received ''"):
            client.workers.resources.with_raw_response.delete(
                resource_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_move(self, client: BrainbaseLabs) -> None:
        resource = client.workers.resources.move(
            resource_id="resourceId",
            worker_id="workerId",
        )
        assert_matches_type(Resource, resource, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_move_with_all_params(self, client: BrainbaseLabs) -> None:
        resource = client.workers.resources.move(
            resource_id="resourceId",
            worker_id="workerId",
            folder_id="folderId",
        )
        assert_matches_type(Resource, resource, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_move(self, client: BrainbaseLabs) -> None:
        response = client.workers.resources.with_raw_response.move(
            resource_id="resourceId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource = response.parse()
        assert_matches_type(Resource, resource, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_move(self, client: BrainbaseLabs) -> None:
        with client.workers.resources.with_streaming_response.move(
            resource_id="resourceId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource = response.parse()
            assert_matches_type(Resource, resource, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_move(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.resources.with_raw_response.move(
                resource_id="resourceId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_id` but received ''"):
            client.workers.resources.with_raw_response.move(
                resource_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_query(self, client: BrainbaseLabs) -> None:
        resource = client.workers.resources.query(
            worker_id="workerId",
            query="query",
        )
        assert_matches_type(ResourceQueryResponse, resource, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_query_with_all_params(self, client: BrainbaseLabs) -> None:
        resource = client.workers.resources.query(
            worker_id="workerId",
            query="query",
            folder_id="folderId",
            folder_name="folderName",
            query_params={
                "max_token_for_global_context": 0,
                "max_token_for_local_context": 0,
                "max_token_for_text_unit": 0,
                "mode": "mode",
                "only_need_context": True,
                "only_need_prompt": True,
                "response_type": "responseType",
                "stream": True,
                "top_k": 0,
            },
            resources=["string"],
        )
        assert_matches_type(ResourceQueryResponse, resource, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_query(self, client: BrainbaseLabs) -> None:
        response = client.workers.resources.with_raw_response.query(
            worker_id="workerId",
            query="query",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource = response.parse()
        assert_matches_type(ResourceQueryResponse, resource, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_query(self, client: BrainbaseLabs) -> None:
        with client.workers.resources.with_streaming_response.query(
            worker_id="workerId",
            query="query",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource = response.parse()
            assert_matches_type(ResourceQueryResponse, resource, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_query(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.resources.with_raw_response.query(
                worker_id="",
                query="query",
            )


class TestAsyncResources:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        resource = await async_client.workers.resources.retrieve(
            resource_id="resourceId",
            worker_id="workerId",
        )
        assert_matches_type(Resource, resource, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.resources.with_raw_response.retrieve(
            resource_id="resourceId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource = await response.parse()
        assert_matches_type(Resource, resource, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.resources.with_streaming_response.retrieve(
            resource_id="resourceId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource = await response.parse()
            assert_matches_type(Resource, resource, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.resources.with_raw_response.retrieve(
                resource_id="resourceId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_id` but received ''"):
            await async_client.workers.resources.with_raw_response.retrieve(
                resource_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        resource = await async_client.workers.resources.delete(
            resource_id="resourceId",
            worker_id="workerId",
        )
        assert resource is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.resources.with_raw_response.delete(
            resource_id="resourceId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource = await response.parse()
        assert resource is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.resources.with_streaming_response.delete(
            resource_id="resourceId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource = await response.parse()
            assert resource is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.resources.with_raw_response.delete(
                resource_id="resourceId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_id` but received ''"):
            await async_client.workers.resources.with_raw_response.delete(
                resource_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_move(self, async_client: AsyncBrainbaseLabs) -> None:
        resource = await async_client.workers.resources.move(
            resource_id="resourceId",
            worker_id="workerId",
        )
        assert_matches_type(Resource, resource, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_move_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        resource = await async_client.workers.resources.move(
            resource_id="resourceId",
            worker_id="workerId",
            folder_id="folderId",
        )
        assert_matches_type(Resource, resource, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_move(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.resources.with_raw_response.move(
            resource_id="resourceId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource = await response.parse()
        assert_matches_type(Resource, resource, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_move(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.resources.with_streaming_response.move(
            resource_id="resourceId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource = await response.parse()
            assert_matches_type(Resource, resource, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_move(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.resources.with_raw_response.move(
                resource_id="resourceId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_id` but received ''"):
            await async_client.workers.resources.with_raw_response.move(
                resource_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_query(self, async_client: AsyncBrainbaseLabs) -> None:
        resource = await async_client.workers.resources.query(
            worker_id="workerId",
            query="query",
        )
        assert_matches_type(ResourceQueryResponse, resource, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_query_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        resource = await async_client.workers.resources.query(
            worker_id="workerId",
            query="query",
            folder_id="folderId",
            folder_name="folderName",
            query_params={
                "max_token_for_global_context": 0,
                "max_token_for_local_context": 0,
                "max_token_for_text_unit": 0,
                "mode": "mode",
                "only_need_context": True,
                "only_need_prompt": True,
                "response_type": "responseType",
                "stream": True,
                "top_k": 0,
            },
            resources=["string"],
        )
        assert_matches_type(ResourceQueryResponse, resource, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_query(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.resources.with_raw_response.query(
            worker_id="workerId",
            query="query",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource = await response.parse()
        assert_matches_type(ResourceQueryResponse, resource, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_query(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.resources.with_streaming_response.query(
            worker_id="workerId",
            query="query",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource = await response.parse()
            assert_matches_type(ResourceQueryResponse, resource, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_query(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.resources.with_raw_response.query(
                worker_id="",
                query="query",
            )

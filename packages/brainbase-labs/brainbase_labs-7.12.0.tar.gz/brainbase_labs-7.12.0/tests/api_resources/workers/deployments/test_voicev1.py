# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from brainbase_labs import BrainbaseLabs, AsyncBrainbaseLabs
from brainbase_labs.types.shared import VoiceV1Deployment
from brainbase_labs.types.workers.deployments import (
    Voicev1ListResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestVoicev1:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: BrainbaseLabs) -> None:
        voicev1 = client.workers.deployments.voicev1.create(
            worker_id="workerId",
            allowed_transfer_numbers=["string"],
            config={},
            end_sentence="endSentence",
            flow_id="flowId",
            functions="functions",
            language="language",
            model="model",
            name="name",
            objective="objective",
            phone_number="phoneNumber",
            resource_keys=["string"],
            start_sentence="startSentence",
            voice_id="voiceId",
            ws_base_url="wsBaseUrl",
        )
        assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: BrainbaseLabs) -> None:
        voicev1 = client.workers.deployments.voicev1.create(
            worker_id="workerId",
            allowed_transfer_numbers=["string"],
            config={},
            end_sentence="endSentence",
            flow_id="flowId",
            functions="functions",
            language="language",
            model="model",
            name="name",
            objective="objective",
            phone_number="phoneNumber",
            resource_keys=["string"],
            start_sentence="startSentence",
            voice_id="voiceId",
            ws_base_url="wsBaseUrl",
            extractions={
                "foo": {
                    "description": "description",
                    "type": "string",
                    "required": True,
                }
            },
        )
        assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voicev1.with_raw_response.create(
            worker_id="workerId",
            allowed_transfer_numbers=["string"],
            config={},
            end_sentence="endSentence",
            flow_id="flowId",
            functions="functions",
            language="language",
            model="model",
            name="name",
            objective="objective",
            phone_number="phoneNumber",
            resource_keys=["string"],
            start_sentence="startSentence",
            voice_id="voiceId",
            ws_base_url="wsBaseUrl",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voicev1 = response.parse()
        assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voicev1.with_streaming_response.create(
            worker_id="workerId",
            allowed_transfer_numbers=["string"],
            config={},
            end_sentence="endSentence",
            flow_id="flowId",
            functions="functions",
            language="language",
            model="model",
            name="name",
            objective="objective",
            phone_number="phoneNumber",
            resource_keys=["string"],
            start_sentence="startSentence",
            voice_id="voiceId",
            ws_base_url="wsBaseUrl",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voicev1 = response.parse()
            assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voicev1.with_raw_response.create(
                worker_id="",
                allowed_transfer_numbers=["string"],
                config={},
                end_sentence="endSentence",
                flow_id="flowId",
                functions="functions",
                language="language",
                model="model",
                name="name",
                objective="objective",
                phone_number="phoneNumber",
                resource_keys=["string"],
                start_sentence="startSentence",
                voice_id="voiceId",
                ws_base_url="wsBaseUrl",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: BrainbaseLabs) -> None:
        voicev1 = client.workers.deployments.voicev1.retrieve(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voicev1.with_raw_response.retrieve(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voicev1 = response.parse()
        assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voicev1.with_streaming_response.retrieve(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voicev1 = response.parse()
            assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voicev1.with_raw_response.retrieve(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voicev1.with_raw_response.retrieve(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: BrainbaseLabs) -> None:
        voicev1 = client.workers.deployments.voicev1.update(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: BrainbaseLabs) -> None:
        voicev1 = client.workers.deployments.voicev1.update(
            deployment_id="deploymentId",
            worker_id="workerId",
            allowed_transfer_numbers=["string"],
            config="config",
            end_sentence="endSentence",
            extractions={
                "foo": {
                    "description": "description",
                    "type": "string",
                    "required": True,
                }
            },
            flow_id="flowId",
            functions="functions",
            language="language",
            model="model",
            name="name",
            objective="objective",
            phone_number="phoneNumber",
            resource_keys=["string"],
            start_sentence="startSentence",
            voice_id="voiceId",
            ws_base_url="wsBaseUrl",
        )
        assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voicev1.with_raw_response.update(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voicev1 = response.parse()
        assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voicev1.with_streaming_response.update(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voicev1 = response.parse()
            assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voicev1.with_raw_response.update(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voicev1.with_raw_response.update(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: BrainbaseLabs) -> None:
        voicev1 = client.workers.deployments.voicev1.list(
            "workerId",
        )
        assert_matches_type(Voicev1ListResponse, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voicev1.with_raw_response.list(
            "workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voicev1 = response.parse()
        assert_matches_type(Voicev1ListResponse, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voicev1.with_streaming_response.list(
            "workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voicev1 = response.parse()
            assert_matches_type(Voicev1ListResponse, voicev1, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voicev1.with_raw_response.list(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: BrainbaseLabs) -> None:
        voicev1 = client.workers.deployments.voicev1.delete(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert voicev1 is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voicev1.with_raw_response.delete(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voicev1 = response.parse()
        assert voicev1 is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voicev1.with_streaming_response.delete(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voicev1 = response.parse()
            assert voicev1 is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voicev1.with_raw_response.delete(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voicev1.with_raw_response.delete(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_make_batch_calls(self, client: BrainbaseLabs) -> None:
        voicev1 = client.workers.deployments.voicev1.make_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[
                {
                    "id": "id",
                    "phone_number": "phoneNumber",
                }
            ],
        )
        assert voicev1 is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_make_batch_calls_with_all_params(self, client: BrainbaseLabs) -> None:
        voicev1 = client.workers.deployments.voicev1.make_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[
                {
                    "id": "id",
                    "phone_number": "phoneNumber",
                    "status": "PENDING",
                }
            ],
            additional_data={"foo": "string"},
            batch_interval_minutes=0,
            batch_size=0,
            condition="condition",
            extractions={
                "foo": {
                    "description": "description",
                    "type": "string",
                    "example": "example",
                    "required": True,
                }
            },
            ws_url="wsUrl",
        )
        assert voicev1 is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_make_batch_calls(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voicev1.with_raw_response.make_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[
                {
                    "id": "id",
                    "phone_number": "phoneNumber",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voicev1 = response.parse()
        assert voicev1 is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_make_batch_calls(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voicev1.with_streaming_response.make_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[
                {
                    "id": "id",
                    "phone_number": "phoneNumber",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voicev1 = response.parse()
            assert voicev1 is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_make_batch_calls(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voicev1.with_raw_response.make_batch_calls(
                deployment_id="deploymentId",
                worker_id="",
                data=[
                    {
                        "id": "id",
                        "phone_number": "phoneNumber",
                    }
                ],
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voicev1.with_raw_response.make_batch_calls(
                deployment_id="",
                worker_id="workerId",
                data=[
                    {
                        "id": "id",
                        "phone_number": "phoneNumber",
                    }
                ],
            )


class TestAsyncVoicev1:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncBrainbaseLabs) -> None:
        voicev1 = await async_client.workers.deployments.voicev1.create(
            worker_id="workerId",
            allowed_transfer_numbers=["string"],
            config={},
            end_sentence="endSentence",
            flow_id="flowId",
            functions="functions",
            language="language",
            model="model",
            name="name",
            objective="objective",
            phone_number="phoneNumber",
            resource_keys=["string"],
            start_sentence="startSentence",
            voice_id="voiceId",
            ws_base_url="wsBaseUrl",
        )
        assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        voicev1 = await async_client.workers.deployments.voicev1.create(
            worker_id="workerId",
            allowed_transfer_numbers=["string"],
            config={},
            end_sentence="endSentence",
            flow_id="flowId",
            functions="functions",
            language="language",
            model="model",
            name="name",
            objective="objective",
            phone_number="phoneNumber",
            resource_keys=["string"],
            start_sentence="startSentence",
            voice_id="voiceId",
            ws_base_url="wsBaseUrl",
            extractions={
                "foo": {
                    "description": "description",
                    "type": "string",
                    "required": True,
                }
            },
        )
        assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voicev1.with_raw_response.create(
            worker_id="workerId",
            allowed_transfer_numbers=["string"],
            config={},
            end_sentence="endSentence",
            flow_id="flowId",
            functions="functions",
            language="language",
            model="model",
            name="name",
            objective="objective",
            phone_number="phoneNumber",
            resource_keys=["string"],
            start_sentence="startSentence",
            voice_id="voiceId",
            ws_base_url="wsBaseUrl",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voicev1 = await response.parse()
        assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voicev1.with_streaming_response.create(
            worker_id="workerId",
            allowed_transfer_numbers=["string"],
            config={},
            end_sentence="endSentence",
            flow_id="flowId",
            functions="functions",
            language="language",
            model="model",
            name="name",
            objective="objective",
            phone_number="phoneNumber",
            resource_keys=["string"],
            start_sentence="startSentence",
            voice_id="voiceId",
            ws_base_url="wsBaseUrl",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voicev1 = await response.parse()
            assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voicev1.with_raw_response.create(
                worker_id="",
                allowed_transfer_numbers=["string"],
                config={},
                end_sentence="endSentence",
                flow_id="flowId",
                functions="functions",
                language="language",
                model="model",
                name="name",
                objective="objective",
                phone_number="phoneNumber",
                resource_keys=["string"],
                start_sentence="startSentence",
                voice_id="voiceId",
                ws_base_url="wsBaseUrl",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        voicev1 = await async_client.workers.deployments.voicev1.retrieve(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voicev1.with_raw_response.retrieve(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voicev1 = await response.parse()
        assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voicev1.with_streaming_response.retrieve(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voicev1 = await response.parse()
            assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voicev1.with_raw_response.retrieve(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voicev1.with_raw_response.retrieve(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncBrainbaseLabs) -> None:
        voicev1 = await async_client.workers.deployments.voicev1.update(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        voicev1 = await async_client.workers.deployments.voicev1.update(
            deployment_id="deploymentId",
            worker_id="workerId",
            allowed_transfer_numbers=["string"],
            config="config",
            end_sentence="endSentence",
            extractions={
                "foo": {
                    "description": "description",
                    "type": "string",
                    "required": True,
                }
            },
            flow_id="flowId",
            functions="functions",
            language="language",
            model="model",
            name="name",
            objective="objective",
            phone_number="phoneNumber",
            resource_keys=["string"],
            start_sentence="startSentence",
            voice_id="voiceId",
            ws_base_url="wsBaseUrl",
        )
        assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voicev1.with_raw_response.update(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voicev1 = await response.parse()
        assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voicev1.with_streaming_response.update(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voicev1 = await response.parse()
            assert_matches_type(VoiceV1Deployment, voicev1, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voicev1.with_raw_response.update(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voicev1.with_raw_response.update(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncBrainbaseLabs) -> None:
        voicev1 = await async_client.workers.deployments.voicev1.list(
            "workerId",
        )
        assert_matches_type(Voicev1ListResponse, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voicev1.with_raw_response.list(
            "workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voicev1 = await response.parse()
        assert_matches_type(Voicev1ListResponse, voicev1, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voicev1.with_streaming_response.list(
            "workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voicev1 = await response.parse()
            assert_matches_type(Voicev1ListResponse, voicev1, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voicev1.with_raw_response.list(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        voicev1 = await async_client.workers.deployments.voicev1.delete(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert voicev1 is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voicev1.with_raw_response.delete(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voicev1 = await response.parse()
        assert voicev1 is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voicev1.with_streaming_response.delete(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voicev1 = await response.parse()
            assert voicev1 is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voicev1.with_raw_response.delete(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voicev1.with_raw_response.delete(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_make_batch_calls(self, async_client: AsyncBrainbaseLabs) -> None:
        voicev1 = await async_client.workers.deployments.voicev1.make_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[
                {
                    "id": "id",
                    "phone_number": "phoneNumber",
                }
            ],
        )
        assert voicev1 is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_make_batch_calls_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        voicev1 = await async_client.workers.deployments.voicev1.make_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[
                {
                    "id": "id",
                    "phone_number": "phoneNumber",
                    "status": "PENDING",
                }
            ],
            additional_data={"foo": "string"},
            batch_interval_minutes=0,
            batch_size=0,
            condition="condition",
            extractions={
                "foo": {
                    "description": "description",
                    "type": "string",
                    "example": "example",
                    "required": True,
                }
            },
            ws_url="wsUrl",
        )
        assert voicev1 is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_make_batch_calls(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voicev1.with_raw_response.make_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[
                {
                    "id": "id",
                    "phone_number": "phoneNumber",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voicev1 = await response.parse()
        assert voicev1 is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_make_batch_calls(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voicev1.with_streaming_response.make_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[
                {
                    "id": "id",
                    "phone_number": "phoneNumber",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voicev1 = await response.parse()
            assert voicev1 is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_make_batch_calls(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voicev1.with_raw_response.make_batch_calls(
                deployment_id="deploymentId",
                worker_id="",
                data=[
                    {
                        "id": "id",
                        "phone_number": "phoneNumber",
                    }
                ],
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voicev1.with_raw_response.make_batch_calls(
                deployment_id="",
                worker_id="workerId",
                data=[
                    {
                        "id": "id",
                        "phone_number": "phoneNumber",
                    }
                ],
            )

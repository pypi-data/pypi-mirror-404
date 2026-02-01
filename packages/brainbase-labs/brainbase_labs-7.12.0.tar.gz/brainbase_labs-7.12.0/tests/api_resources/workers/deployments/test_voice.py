# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from brainbase_labs import BrainbaseLabs, AsyncBrainbaseLabs
from brainbase_labs.types.shared import VoiceDeployment
from brainbase_labs.types.workers.deployments import (
    VoiceListResponse,
    VoiceStopCampaignResponse,
    VoiceMakeBatchCallsResponse,
    VoiceStopBatchCallsResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestVoice:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: BrainbaseLabs) -> None:
        voice = client.workers.deployments.voice.create(
            worker_id="workerId",
            flow_id="flowId",
            name="name",
            phone_number="phoneNumber",
        )
        assert_matches_type(VoiceDeployment, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: BrainbaseLabs) -> None:
        voice = client.workers.deployments.voice.create(
            worker_id="workerId",
            flow_id="flowId",
            name="name",
            phone_number="phoneNumber",
            backup_phone_message="backupPhoneMessage",
            backup_phone_number="backupPhoneNumber",
            enable_voice_sentiment=True,
            engine_model="engineModel",
            external_config={
                "ambient_sound": "ambientSound",
                "ambient_sound_volume": 0,
                "audio_encoding": "audioEncoding",
                "backchannel_frequency": 0,
                "backchannel_words": ["string"],
                "begin_message_delay_ms": 0,
                "boosted_keywords": ["string"],
                "enable_backchannel": True,
                "enable_responsive_reactions": True,
                "enable_transcription_formatting": True,
                "enable_voicemail_detection": True,
                "end_call_after_silence_ms": 0,
                "engine_version": "engineVersion",
                "fallback_voice_ids": ["string"],
                "filler_audio_enabled": True,
                "include_reason": True,
                "interruptibility": 0,
                "language": "language",
                "max_call_duration_ms": 0,
                "normalize_for_speech": True,
                "opt_out_sensitive_data_storage": True,
                "pii_config": {
                    "mode": "off",
                    "categories": ["string"],
                },
                "pronunciation_dictionary": [
                    {
                        "alphabet": "ipa",
                        "phoneme": "phoneme",
                        "word": "word",
                    }
                ],
                "reduce_silence": True,
                "reminder_max_count": 0,
                "reminder_trigger_ms": 0,
                "responsiveness": 0,
                "responsive_reactions_frequency": 0,
                "responsive_reactions_words": ["string"],
                "ring_duration_ms": 0,
                "sample_rate": 0,
                "voice_emotion_enabled": True,
                "voice_id": "voiceId",
                "voicemail_detection_timeout_ms": 0,
                "voicemail_message": "voicemailMessage",
                "voice_model": "eleven_turbo_v2",
                "voice_speed": 0,
                "voice_temperature": 0,
                "volume": 0,
            },
            extractions={
                "foo": {
                    "description": "description",
                    "type": "string",
                    "required": True,
                }
            },
            success_criteria=[
                {
                    "items": [
                        {
                            "description": "description",
                            "threshold": 0,
                            "title": "title",
                            "type": "BINARY",
                        }
                    ],
                    "title": "title",
                    "description": "description",
                }
            ],
        )
        assert_matches_type(VoiceDeployment, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.with_raw_response.create(
            worker_id="workerId",
            flow_id="flowId",
            name="name",
            phone_number="phoneNumber",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice = response.parse()
        assert_matches_type(VoiceDeployment, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.with_streaming_response.create(
            worker_id="workerId",
            flow_id="flowId",
            name="name",
            phone_number="phoneNumber",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice = response.parse()
            assert_matches_type(VoiceDeployment, voice, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.with_raw_response.create(
                worker_id="",
                flow_id="flowId",
                name="name",
                phone_number="phoneNumber",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: BrainbaseLabs) -> None:
        voice = client.workers.deployments.voice.retrieve(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert_matches_type(VoiceDeployment, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.with_raw_response.retrieve(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice = response.parse()
        assert_matches_type(VoiceDeployment, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.with_streaming_response.retrieve(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice = response.parse()
            assert_matches_type(VoiceDeployment, voice, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.with_raw_response.retrieve(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voice.with_raw_response.retrieve(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: BrainbaseLabs) -> None:
        voice = client.workers.deployments.voice.update(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert_matches_type(VoiceDeployment, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: BrainbaseLabs) -> None:
        voice = client.workers.deployments.voice.update(
            deployment_id="deploymentId",
            worker_id="workerId",
            backup_phone_message="backupPhoneMessage",
            backup_phone_number="backupPhoneNumber",
            custom_webhooks=[{"url": "url"}],
            enable_voice_sentiment=True,
            engine_model="engineModel",
            external_config={
                "ambient_sound": "ambientSound",
                "ambient_sound_volume": 0,
                "audio_encoding": "audioEncoding",
                "backchannel_frequency": 0,
                "backchannel_words": ["string"],
                "begin_message_delay_ms": 0,
                "boosted_keywords": ["string"],
                "enable_backchannel": True,
                "enable_responsive_reactions": True,
                "enable_transcription_formatting": True,
                "enable_voicemail_detection": True,
                "end_call_after_silence_ms": 0,
                "engine_version": "engineVersion",
                "fallback_voice_ids": ["string"],
                "filler_audio_enabled": True,
                "include_reason": True,
                "interruptibility": 0,
                "language": "language",
                "max_call_duration_ms": 0,
                "normalize_for_speech": True,
                "opt_out_sensitive_data_storage": True,
                "pii_config": {
                    "mode": "off",
                    "categories": ["string"],
                },
                "pronunciation_dictionary": [
                    {
                        "alphabet": "ipa",
                        "phoneme": "phoneme",
                        "word": "word",
                    }
                ],
                "reduce_silence": True,
                "reminder_max_count": 0,
                "reminder_trigger_ms": 0,
                "responsiveness": 0,
                "responsive_reactions_frequency": 0,
                "responsive_reactions_words": ["string"],
                "ring_duration_ms": 0,
                "sample_rate": 0,
                "voice_emotion_enabled": True,
                "voice_id": "voiceId",
                "voicemail_detection_timeout_ms": 0,
                "voicemail_message": "voicemailMessage",
                "voice_model": "eleven_turbo_v2",
                "voice_speed": 0,
                "voice_temperature": 0,
                "volume": 0,
            },
            extractions={
                "foo": {
                    "description": "description",
                    "type": "string",
                    "required": True,
                }
            },
            flow_id="flowId",
            name="name",
            phone_number="phoneNumber",
            success_criteria=[
                {
                    "items": [
                        {
                            "description": "description",
                            "threshold": 0,
                            "title": "title",
                            "type": "BINARY",
                        }
                    ],
                    "title": "title",
                    "description": "description",
                }
            ],
        )
        assert_matches_type(VoiceDeployment, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.with_raw_response.update(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice = response.parse()
        assert_matches_type(VoiceDeployment, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.with_streaming_response.update(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice = response.parse()
            assert_matches_type(VoiceDeployment, voice, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.with_raw_response.update(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voice.with_raw_response.update(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: BrainbaseLabs) -> None:
        voice = client.workers.deployments.voice.list(
            "workerId",
        )
        assert_matches_type(VoiceListResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.with_raw_response.list(
            "workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice = response.parse()
        assert_matches_type(VoiceListResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.with_streaming_response.list(
            "workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice = response.parse()
            assert_matches_type(VoiceListResponse, voice, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.with_raw_response.list(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: BrainbaseLabs) -> None:
        voice = client.workers.deployments.voice.delete(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert voice is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.with_raw_response.delete(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice = response.parse()
        assert voice is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.with_streaming_response.delete(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice = response.parse()
            assert voice is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.with_raw_response.delete(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voice.with_raw_response.delete(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_make_batch_calls(self, client: BrainbaseLabs) -> None:
        voice = client.workers.deployments.voice.make_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[{"foo": "string"}],
        )
        assert_matches_type(VoiceMakeBatchCallsResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_make_batch_calls_with_all_params(self, client: BrainbaseLabs) -> None:
        voice = client.workers.deployments.voice.make_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[{"foo": "string"}],
            additional_data="additional_data",
            batch_interval_minutes=0,
            batch_size=0,
            condition="condition",
            country="country",
            extractions="extractions",
            ws_url="wsUrl",
        )
        assert_matches_type(VoiceMakeBatchCallsResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_make_batch_calls(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.with_raw_response.make_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[{"foo": "string"}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice = response.parse()
        assert_matches_type(VoiceMakeBatchCallsResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_make_batch_calls(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.with_streaming_response.make_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[{"foo": "string"}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice = response.parse()
            assert_matches_type(VoiceMakeBatchCallsResponse, voice, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_make_batch_calls(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.with_raw_response.make_batch_calls(
                deployment_id="deploymentId",
                worker_id="",
                data=[{"foo": "string"}],
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voice.with_raw_response.make_batch_calls(
                deployment_id="",
                worker_id="workerId",
                data=[{"foo": "string"}],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_stop_batch_calls(self, client: BrainbaseLabs) -> None:
        voice = client.workers.deployments.voice.stop_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert_matches_type(VoiceStopBatchCallsResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_stop_batch_calls(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.with_raw_response.stop_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice = response.parse()
        assert_matches_type(VoiceStopBatchCallsResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_stop_batch_calls(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.with_streaming_response.stop_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice = response.parse()
            assert_matches_type(VoiceStopBatchCallsResponse, voice, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_stop_batch_calls(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.with_raw_response.stop_batch_calls(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voice.with_raw_response.stop_batch_calls(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_stop_campaign(self, client: BrainbaseLabs) -> None:
        voice = client.workers.deployments.voice.stop_campaign(
            deployment_id="deploymentId",
            worker_id="workerId",
            campaign_id="campaign_id",
        )
        assert_matches_type(VoiceStopCampaignResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_stop_campaign(self, client: BrainbaseLabs) -> None:
        response = client.workers.deployments.voice.with_raw_response.stop_campaign(
            deployment_id="deploymentId",
            worker_id="workerId",
            campaign_id="campaign_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice = response.parse()
        assert_matches_type(VoiceStopCampaignResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_stop_campaign(self, client: BrainbaseLabs) -> None:
        with client.workers.deployments.voice.with_streaming_response.stop_campaign(
            deployment_id="deploymentId",
            worker_id="workerId",
            campaign_id="campaign_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice = response.parse()
            assert_matches_type(VoiceStopCampaignResponse, voice, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_stop_campaign(self, client: BrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            client.workers.deployments.voice.with_raw_response.stop_campaign(
                deployment_id="deploymentId",
                worker_id="",
                campaign_id="campaign_id",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            client.workers.deployments.voice.with_raw_response.stop_campaign(
                deployment_id="",
                worker_id="workerId",
                campaign_id="campaign_id",
            )


class TestAsyncVoice:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncBrainbaseLabs) -> None:
        voice = await async_client.workers.deployments.voice.create(
            worker_id="workerId",
            flow_id="flowId",
            name="name",
            phone_number="phoneNumber",
        )
        assert_matches_type(VoiceDeployment, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        voice = await async_client.workers.deployments.voice.create(
            worker_id="workerId",
            flow_id="flowId",
            name="name",
            phone_number="phoneNumber",
            backup_phone_message="backupPhoneMessage",
            backup_phone_number="backupPhoneNumber",
            enable_voice_sentiment=True,
            engine_model="engineModel",
            external_config={
                "ambient_sound": "ambientSound",
                "ambient_sound_volume": 0,
                "audio_encoding": "audioEncoding",
                "backchannel_frequency": 0,
                "backchannel_words": ["string"],
                "begin_message_delay_ms": 0,
                "boosted_keywords": ["string"],
                "enable_backchannel": True,
                "enable_responsive_reactions": True,
                "enable_transcription_formatting": True,
                "enable_voicemail_detection": True,
                "end_call_after_silence_ms": 0,
                "engine_version": "engineVersion",
                "fallback_voice_ids": ["string"],
                "filler_audio_enabled": True,
                "include_reason": True,
                "interruptibility": 0,
                "language": "language",
                "max_call_duration_ms": 0,
                "normalize_for_speech": True,
                "opt_out_sensitive_data_storage": True,
                "pii_config": {
                    "mode": "off",
                    "categories": ["string"],
                },
                "pronunciation_dictionary": [
                    {
                        "alphabet": "ipa",
                        "phoneme": "phoneme",
                        "word": "word",
                    }
                ],
                "reduce_silence": True,
                "reminder_max_count": 0,
                "reminder_trigger_ms": 0,
                "responsiveness": 0,
                "responsive_reactions_frequency": 0,
                "responsive_reactions_words": ["string"],
                "ring_duration_ms": 0,
                "sample_rate": 0,
                "voice_emotion_enabled": True,
                "voice_id": "voiceId",
                "voicemail_detection_timeout_ms": 0,
                "voicemail_message": "voicemailMessage",
                "voice_model": "eleven_turbo_v2",
                "voice_speed": 0,
                "voice_temperature": 0,
                "volume": 0,
            },
            extractions={
                "foo": {
                    "description": "description",
                    "type": "string",
                    "required": True,
                }
            },
            success_criteria=[
                {
                    "items": [
                        {
                            "description": "description",
                            "threshold": 0,
                            "title": "title",
                            "type": "BINARY",
                        }
                    ],
                    "title": "title",
                    "description": "description",
                }
            ],
        )
        assert_matches_type(VoiceDeployment, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.with_raw_response.create(
            worker_id="workerId",
            flow_id="flowId",
            name="name",
            phone_number="phoneNumber",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice = await response.parse()
        assert_matches_type(VoiceDeployment, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.with_streaming_response.create(
            worker_id="workerId",
            flow_id="flowId",
            name="name",
            phone_number="phoneNumber",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice = await response.parse()
            assert_matches_type(VoiceDeployment, voice, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.with_raw_response.create(
                worker_id="",
                flow_id="flowId",
                name="name",
                phone_number="phoneNumber",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        voice = await async_client.workers.deployments.voice.retrieve(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert_matches_type(VoiceDeployment, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.with_raw_response.retrieve(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice = await response.parse()
        assert_matches_type(VoiceDeployment, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.with_streaming_response.retrieve(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice = await response.parse()
            assert_matches_type(VoiceDeployment, voice, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.with_raw_response.retrieve(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voice.with_raw_response.retrieve(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncBrainbaseLabs) -> None:
        voice = await async_client.workers.deployments.voice.update(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert_matches_type(VoiceDeployment, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        voice = await async_client.workers.deployments.voice.update(
            deployment_id="deploymentId",
            worker_id="workerId",
            backup_phone_message="backupPhoneMessage",
            backup_phone_number="backupPhoneNumber",
            custom_webhooks=[{"url": "url"}],
            enable_voice_sentiment=True,
            engine_model="engineModel",
            external_config={
                "ambient_sound": "ambientSound",
                "ambient_sound_volume": 0,
                "audio_encoding": "audioEncoding",
                "backchannel_frequency": 0,
                "backchannel_words": ["string"],
                "begin_message_delay_ms": 0,
                "boosted_keywords": ["string"],
                "enable_backchannel": True,
                "enable_responsive_reactions": True,
                "enable_transcription_formatting": True,
                "enable_voicemail_detection": True,
                "end_call_after_silence_ms": 0,
                "engine_version": "engineVersion",
                "fallback_voice_ids": ["string"],
                "filler_audio_enabled": True,
                "include_reason": True,
                "interruptibility": 0,
                "language": "language",
                "max_call_duration_ms": 0,
                "normalize_for_speech": True,
                "opt_out_sensitive_data_storage": True,
                "pii_config": {
                    "mode": "off",
                    "categories": ["string"],
                },
                "pronunciation_dictionary": [
                    {
                        "alphabet": "ipa",
                        "phoneme": "phoneme",
                        "word": "word",
                    }
                ],
                "reduce_silence": True,
                "reminder_max_count": 0,
                "reminder_trigger_ms": 0,
                "responsiveness": 0,
                "responsive_reactions_frequency": 0,
                "responsive_reactions_words": ["string"],
                "ring_duration_ms": 0,
                "sample_rate": 0,
                "voice_emotion_enabled": True,
                "voice_id": "voiceId",
                "voicemail_detection_timeout_ms": 0,
                "voicemail_message": "voicemailMessage",
                "voice_model": "eleven_turbo_v2",
                "voice_speed": 0,
                "voice_temperature": 0,
                "volume": 0,
            },
            extractions={
                "foo": {
                    "description": "description",
                    "type": "string",
                    "required": True,
                }
            },
            flow_id="flowId",
            name="name",
            phone_number="phoneNumber",
            success_criteria=[
                {
                    "items": [
                        {
                            "description": "description",
                            "threshold": 0,
                            "title": "title",
                            "type": "BINARY",
                        }
                    ],
                    "title": "title",
                    "description": "description",
                }
            ],
        )
        assert_matches_type(VoiceDeployment, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.with_raw_response.update(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice = await response.parse()
        assert_matches_type(VoiceDeployment, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.with_streaming_response.update(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice = await response.parse()
            assert_matches_type(VoiceDeployment, voice, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.with_raw_response.update(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voice.with_raw_response.update(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncBrainbaseLabs) -> None:
        voice = await async_client.workers.deployments.voice.list(
            "workerId",
        )
        assert_matches_type(VoiceListResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.with_raw_response.list(
            "workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice = await response.parse()
        assert_matches_type(VoiceListResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.with_streaming_response.list(
            "workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice = await response.parse()
            assert_matches_type(VoiceListResponse, voice, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.with_raw_response.list(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        voice = await async_client.workers.deployments.voice.delete(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert voice is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.with_raw_response.delete(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice = await response.parse()
        assert voice is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.with_streaming_response.delete(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice = await response.parse()
            assert voice is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.with_raw_response.delete(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voice.with_raw_response.delete(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_make_batch_calls(self, async_client: AsyncBrainbaseLabs) -> None:
        voice = await async_client.workers.deployments.voice.make_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[{"foo": "string"}],
        )
        assert_matches_type(VoiceMakeBatchCallsResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_make_batch_calls_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        voice = await async_client.workers.deployments.voice.make_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[{"foo": "string"}],
            additional_data="additional_data",
            batch_interval_minutes=0,
            batch_size=0,
            condition="condition",
            country="country",
            extractions="extractions",
            ws_url="wsUrl",
        )
        assert_matches_type(VoiceMakeBatchCallsResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_make_batch_calls(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.with_raw_response.make_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[{"foo": "string"}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice = await response.parse()
        assert_matches_type(VoiceMakeBatchCallsResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_make_batch_calls(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.with_streaming_response.make_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
            data=[{"foo": "string"}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice = await response.parse()
            assert_matches_type(VoiceMakeBatchCallsResponse, voice, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_make_batch_calls(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.with_raw_response.make_batch_calls(
                deployment_id="deploymentId",
                worker_id="",
                data=[{"foo": "string"}],
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voice.with_raw_response.make_batch_calls(
                deployment_id="",
                worker_id="workerId",
                data=[{"foo": "string"}],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_stop_batch_calls(self, async_client: AsyncBrainbaseLabs) -> None:
        voice = await async_client.workers.deployments.voice.stop_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
        )
        assert_matches_type(VoiceStopBatchCallsResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_stop_batch_calls(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.with_raw_response.stop_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice = await response.parse()
        assert_matches_type(VoiceStopBatchCallsResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_stop_batch_calls(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.with_streaming_response.stop_batch_calls(
            deployment_id="deploymentId",
            worker_id="workerId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice = await response.parse()
            assert_matches_type(VoiceStopBatchCallsResponse, voice, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_stop_batch_calls(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.with_raw_response.stop_batch_calls(
                deployment_id="deploymentId",
                worker_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voice.with_raw_response.stop_batch_calls(
                deployment_id="",
                worker_id="workerId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_stop_campaign(self, async_client: AsyncBrainbaseLabs) -> None:
        voice = await async_client.workers.deployments.voice.stop_campaign(
            deployment_id="deploymentId",
            worker_id="workerId",
            campaign_id="campaign_id",
        )
        assert_matches_type(VoiceStopCampaignResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_stop_campaign(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.workers.deployments.voice.with_raw_response.stop_campaign(
            deployment_id="deploymentId",
            worker_id="workerId",
            campaign_id="campaign_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice = await response.parse()
        assert_matches_type(VoiceStopCampaignResponse, voice, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_stop_campaign(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.workers.deployments.voice.with_streaming_response.stop_campaign(
            deployment_id="deploymentId",
            worker_id="workerId",
            campaign_id="campaign_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice = await response.parse()
            assert_matches_type(VoiceStopCampaignResponse, voice, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_stop_campaign(self, async_client: AsyncBrainbaseLabs) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `worker_id` but received ''"):
            await async_client.workers.deployments.voice.with_raw_response.stop_campaign(
                deployment_id="deploymentId",
                worker_id="",
                campaign_id="campaign_id",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `deployment_id` but received ''"):
            await async_client.workers.deployments.voice.with_raw_response.stop_campaign(
                deployment_id="",
                worker_id="workerId",
                campaign_id="campaign_id",
            )

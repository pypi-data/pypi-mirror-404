# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from brainbase_labs import BrainbaseLabs, AsyncBrainbaseLabs
from brainbase_labs.types import VoiceAnalysisAnalyzeResponse
from brainbase_labs._utils import parse_datetime

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestVoiceAnalysis:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_analyze(self, client: BrainbaseLabs) -> None:
        voice_analysis = client.voice_analysis.analyze()
        assert_matches_type(VoiceAnalysisAnalyzeResponse, voice_analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_analyze_with_all_params(self, client: BrainbaseLabs) -> None:
        voice_analysis = client.voice_analysis.analyze(
            deployment_ids=["string"],
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            granularity="daily",
            include_call_details=True,
            include_transfers=True,
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            timezone="timezone",
            worker_id="workerId",
        )
        assert_matches_type(VoiceAnalysisAnalyzeResponse, voice_analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_analyze(self, client: BrainbaseLabs) -> None:
        response = client.voice_analysis.with_raw_response.analyze()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice_analysis = response.parse()
        assert_matches_type(VoiceAnalysisAnalyzeResponse, voice_analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_analyze(self, client: BrainbaseLabs) -> None:
        with client.voice_analysis.with_streaming_response.analyze() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice_analysis = response.parse()
            assert_matches_type(VoiceAnalysisAnalyzeResponse, voice_analysis, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncVoiceAnalysis:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_analyze(self, async_client: AsyncBrainbaseLabs) -> None:
        voice_analysis = await async_client.voice_analysis.analyze()
        assert_matches_type(VoiceAnalysisAnalyzeResponse, voice_analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_analyze_with_all_params(self, async_client: AsyncBrainbaseLabs) -> None:
        voice_analysis = await async_client.voice_analysis.analyze(
            deployment_ids=["string"],
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            granularity="daily",
            include_call_details=True,
            include_transfers=True,
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            timezone="timezone",
            worker_id="workerId",
        )
        assert_matches_type(VoiceAnalysisAnalyzeResponse, voice_analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_analyze(self, async_client: AsyncBrainbaseLabs) -> None:
        response = await async_client.voice_analysis.with_raw_response.analyze()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        voice_analysis = await response.parse()
        assert_matches_type(VoiceAnalysisAnalyzeResponse, voice_analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_analyze(self, async_client: AsyncBrainbaseLabs) -> None:
        async with async_client.voice_analysis.with_streaming_response.analyze() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            voice_analysis = await response.parse()
            assert_matches_type(VoiceAnalysisAnalyzeResponse, voice_analysis, path=["response"])

        assert cast(Any, response.is_closed) is True

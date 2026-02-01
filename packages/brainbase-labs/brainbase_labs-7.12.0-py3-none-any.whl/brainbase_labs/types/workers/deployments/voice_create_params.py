# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable, Optional
from typing_extensions import Literal, Required, Annotated, TypedDict

from ...._types import SequenceNotStr
from ...._utils import PropertyInfo

__all__ = [
    "VoiceCreateParams",
    "ExternalConfig",
    "ExternalConfigPiiConfig",
    "ExternalConfigPronunciationDictionary",
    "Extractions",
    "SuccessCriterion",
    "SuccessCriterionItem",
]


class VoiceCreateParams(TypedDict, total=False):
    flow_id: Required[Annotated[str, PropertyInfo(alias="flowId")]]

    name: Required[str]

    phone_number: Required[Annotated[str, PropertyInfo(alias="phoneNumber")]]

    backup_phone_message: Annotated[str, PropertyInfo(alias="backupPhoneMessage")]

    backup_phone_number: Annotated[str, PropertyInfo(alias="backupPhoneNumber")]

    enable_voice_sentiment: Annotated[bool, PropertyInfo(alias="enableVoiceSentiment")]

    engine_model: Annotated[Optional[str], PropertyInfo(alias="engineModel")]

    external_config: Annotated[ExternalConfig, PropertyInfo(alias="externalConfig")]

    extractions: Dict[str, Extractions]

    success_criteria: Annotated[Iterable[SuccessCriterion], PropertyInfo(alias="successCriteria")]


class ExternalConfigPiiConfig(TypedDict, total=False):
    mode: Required[Literal["off", "streaming", "post_call"]]

    categories: SequenceNotStr[str]


class ExternalConfigPronunciationDictionary(TypedDict, total=False):
    alphabet: Required[Literal["ipa", "cmu"]]

    phoneme: Required[str]

    word: Required[str]


class ExternalConfig(TypedDict, total=False):
    ambient_sound: Annotated[Optional[str], PropertyInfo(alias="ambientSound")]

    ambient_sound_volume: Annotated[Optional[float], PropertyInfo(alias="ambientSoundVolume")]

    audio_encoding: Annotated[Optional[str], PropertyInfo(alias="audioEncoding")]

    backchannel_frequency: Annotated[Optional[float], PropertyInfo(alias="backchannelFrequency")]

    backchannel_words: Annotated[Optional[SequenceNotStr[str]], PropertyInfo(alias="backchannelWords")]

    begin_message_delay_ms: Annotated[Optional[float], PropertyInfo(alias="beginMessageDelayMs")]

    boosted_keywords: Annotated[Optional[SequenceNotStr[str]], PropertyInfo(alias="boostedKeywords")]

    enable_backchannel: Annotated[Optional[bool], PropertyInfo(alias="enableBackchannel")]

    enable_responsive_reactions: Annotated[Optional[bool], PropertyInfo(alias="enableResponsiveReactions")]

    enable_transcription_formatting: Annotated[Optional[bool], PropertyInfo(alias="enableTranscriptionFormatting")]

    enable_voicemail_detection: Annotated[Optional[bool], PropertyInfo(alias="enableVoicemailDetection")]

    end_call_after_silence_ms: Annotated[Optional[float], PropertyInfo(alias="endCallAfterSilenceMs")]

    engine_version: Annotated[Optional[str], PropertyInfo(alias="engineVersion")]

    fallback_voice_ids: Annotated[Optional[SequenceNotStr[str]], PropertyInfo(alias="fallbackVoiceIds")]

    filler_audio_enabled: Annotated[Optional[bool], PropertyInfo(alias="fillerAudioEnabled")]

    include_reason: Annotated[Optional[bool], PropertyInfo(alias="includeReason")]

    interruptibility: Optional[float]

    language: Optional[str]

    max_call_duration_ms: Annotated[Optional[float], PropertyInfo(alias="maxCallDurationMs")]

    normalize_for_speech: Annotated[Optional[bool], PropertyInfo(alias="normalizeForSpeech")]

    opt_out_sensitive_data_storage: Annotated[Optional[bool], PropertyInfo(alias="optOutSensitiveDataStorage")]

    pii_config: Annotated[Optional[ExternalConfigPiiConfig], PropertyInfo(alias="piiConfig")]

    pronunciation_dictionary: Annotated[
        Optional[Iterable[ExternalConfigPronunciationDictionary]], PropertyInfo(alias="pronunciationDictionary")
    ]

    reduce_silence: Annotated[Optional[bool], PropertyInfo(alias="reduceSilence")]

    reminder_max_count: Annotated[Optional[float], PropertyInfo(alias="reminderMaxCount")]

    reminder_trigger_ms: Annotated[Optional[float], PropertyInfo(alias="reminderTriggerMs")]

    responsiveness: Optional[float]

    responsive_reactions_frequency: Annotated[Optional[float], PropertyInfo(alias="responsiveReactionsFrequency")]

    responsive_reactions_words: Annotated[Optional[SequenceNotStr[str]], PropertyInfo(alias="responsiveReactionsWords")]

    ring_duration_ms: Annotated[Optional[float], PropertyInfo(alias="ringDurationMs")]

    sample_rate: Annotated[Optional[float], PropertyInfo(alias="sampleRate")]

    voice_emotion_enabled: Annotated[Optional[bool], PropertyInfo(alias="voiceEmotionEnabled")]

    voice_id: Annotated[Optional[str], PropertyInfo(alias="voiceId")]

    voicemail_detection_timeout_ms: Annotated[Optional[float], PropertyInfo(alias="voicemailDetectionTimeoutMs")]

    voicemail_message: Annotated[Optional[str], PropertyInfo(alias="voicemailMessage")]

    voice_model: Annotated[
        Optional[
            Literal[
                "eleven_turbo_v2",
                "eleven_flash_v2",
                "eleven_turbo_v2_5",
                "eleven_flash_v2_5",
                "eleven_multilingual_v2",
                "Play3.0-mini",
                "PlayDialog",
            ]
        ],
        PropertyInfo(alias="voiceModel"),
    ]

    voice_speed: Annotated[Optional[float], PropertyInfo(alias="voiceSpeed")]

    voice_temperature: Annotated[Optional[float], PropertyInfo(alias="voiceTemperature")]

    volume: Optional[float]


class Extractions(TypedDict, total=False):
    description: Required[str]

    type: Required[Literal["string", "number", "boolean"]]

    required: bool


class SuccessCriterionItem(TypedDict, total=False):
    description: Required[str]

    threshold: Required[float]

    title: Required[str]

    type: Required[Literal["BINARY", "SCORE"]]


class SuccessCriterion(TypedDict, total=False):
    items: Required[Iterable[SuccessCriterionItem]]

    title: Required[str]

    description: str

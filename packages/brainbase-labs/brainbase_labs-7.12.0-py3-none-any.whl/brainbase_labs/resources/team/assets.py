# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ..._types import Body, Omit, Query, Headers, NoneType, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...types.team import (
    asset_list_phone_numbers_params,
    asset_register_phone_number_params,
    asset_purchase_phone_numbers_params,
    asset_purchase_whatsapp_sender_params,
    asset_list_available_phone_numbers_params,
)
from ..._base_client import make_request_options
from ...types.team.asset_list_phone_numbers_response import AssetListPhoneNumbersResponse
from ...types.team.asset_register_phone_number_response import AssetRegisterPhoneNumberResponse

__all__ = ["AssetsResource", "AsyncAssetsResource"]


class AssetsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AssetsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AssetsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AssetsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AssetsResourceWithStreamingResponse(self)

    def delete_phone_number(
        self,
        phone_number_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a registered phone number for the team.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not phone_number_id:
            raise ValueError(f"Expected a non-empty value for `phone_number_id` but received {phone_number_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/api/team/assets/phone_numbers/{phone_number_id}/delete",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def list_available_phone_numbers(
        self,
        *,
        country_code: str,
        number_type: Literal["Local", "Mobile", "TollFree"],
        area_code: str | Omit = omit,
        contains: str | Omit = omit,
        mms_enabled: bool | Omit = omit,
        sms_enabled: bool | Omit = omit,
        voice_enabled: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Search for available phone numbers to purchase via Brainbase.

        Args:
          country_code: Two-letter ISO country code (e.g. US, GB).

          number_type: Type of phone number.

          area_code: Filter by area code.

          contains: Filter by pattern contained in number.

          mms_enabled: Filter for MMS-enabled numbers.

          sms_enabled: Filter for SMS-enabled numbers.

          voice_enabled: Filter for voice-enabled numbers.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._get(
            "/api/team/assets/available_phone_numbers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "country_code": country_code,
                        "number_type": number_type,
                        "area_code": area_code,
                        "contains": contains,
                        "mms_enabled": mms_enabled,
                        "sms_enabled": sms_enabled,
                        "voice_enabled": voice_enabled,
                    },
                    asset_list_available_phone_numbers_params.AssetListAvailablePhoneNumbersParams,
                ),
            ),
            cast_to=NoneType,
        )

    def list_phone_numbers(
        self,
        *,
        integration_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AssetListPhoneNumbersResponse:
        """
        Get all registered phone numbers for the team, optionally filtered by
        integration id.

        Args:
          integration_id: Filter phone numbers by integration id.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/api/team/assets/phone_numbers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"integration_id": integration_id}, asset_list_phone_numbers_params.AssetListPhoneNumbersParams
                ),
            ),
            cast_to=AssetListPhoneNumbersResponse,
        )

    def purchase_phone_numbers(
        self,
        *,
        phone_numbers: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Purchase phone numbers via Brainbase Twilio account.

        Args:
          phone_numbers: Array of phone numbers to purchase in E.164 format.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/api/team/assets/purchase_phone_numbers",
            body=maybe_transform(
                {"phone_numbers": phone_numbers}, asset_purchase_phone_numbers_params.AssetPurchasePhoneNumbersParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def purchase_whatsapp_sender(
        self,
        *,
        phone_number: str,
        profile: asset_purchase_whatsapp_sender_params.Profile,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Purchase a phone number and register it as a WhatsApp sender.

        Args:
          phone_number: Phone number in E.164 format.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/api/team/assets/purchase_whatsapp_sender",
            body=maybe_transform(
                {
                    "phone_number": phone_number,
                    "profile": profile,
                },
                asset_purchase_whatsapp_sender_params.AssetPurchaseWhatsappSenderParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def register_phone_number(
        self,
        *,
        integration_id: str,
        phone_number: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AssetRegisterPhoneNumberResponse:
        """
        Register a phone number for the team via Twilio integration.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/team/assets/register_phone_number",
            body=maybe_transform(
                {
                    "integration_id": integration_id,
                    "phone_number": phone_number,
                },
                asset_register_phone_number_params.AssetRegisterPhoneNumberParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AssetRegisterPhoneNumberResponse,
        )

    def retrieve_whatsapp_sender_status(
        self,
        sender_sid: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Get the status of a WhatsApp sender.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not sender_sid:
            raise ValueError(f"Expected a non-empty value for `sender_sid` but received {sender_sid!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._get(
            f"/api/team/assets/whatsapp_sender_status/{sender_sid}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncAssetsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncAssetsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncAssetsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAssetsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/BrainbaseHQ/brainbase-labs-python-sdk#with_streaming_response
        """
        return AsyncAssetsResourceWithStreamingResponse(self)

    async def delete_phone_number(
        self,
        phone_number_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a registered phone number for the team.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not phone_number_id:
            raise ValueError(f"Expected a non-empty value for `phone_number_id` but received {phone_number_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/api/team/assets/phone_numbers/{phone_number_id}/delete",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def list_available_phone_numbers(
        self,
        *,
        country_code: str,
        number_type: Literal["Local", "Mobile", "TollFree"],
        area_code: str | Omit = omit,
        contains: str | Omit = omit,
        mms_enabled: bool | Omit = omit,
        sms_enabled: bool | Omit = omit,
        voice_enabled: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Search for available phone numbers to purchase via Brainbase.

        Args:
          country_code: Two-letter ISO country code (e.g. US, GB).

          number_type: Type of phone number.

          area_code: Filter by area code.

          contains: Filter by pattern contained in number.

          mms_enabled: Filter for MMS-enabled numbers.

          sms_enabled: Filter for SMS-enabled numbers.

          voice_enabled: Filter for voice-enabled numbers.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._get(
            "/api/team/assets/available_phone_numbers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "country_code": country_code,
                        "number_type": number_type,
                        "area_code": area_code,
                        "contains": contains,
                        "mms_enabled": mms_enabled,
                        "sms_enabled": sms_enabled,
                        "voice_enabled": voice_enabled,
                    },
                    asset_list_available_phone_numbers_params.AssetListAvailablePhoneNumbersParams,
                ),
            ),
            cast_to=NoneType,
        )

    async def list_phone_numbers(
        self,
        *,
        integration_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AssetListPhoneNumbersResponse:
        """
        Get all registered phone numbers for the team, optionally filtered by
        integration id.

        Args:
          integration_id: Filter phone numbers by integration id.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/api/team/assets/phone_numbers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"integration_id": integration_id}, asset_list_phone_numbers_params.AssetListPhoneNumbersParams
                ),
            ),
            cast_to=AssetListPhoneNumbersResponse,
        )

    async def purchase_phone_numbers(
        self,
        *,
        phone_numbers: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Purchase phone numbers via Brainbase Twilio account.

        Args:
          phone_numbers: Array of phone numbers to purchase in E.164 format.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/api/team/assets/purchase_phone_numbers",
            body=await async_maybe_transform(
                {"phone_numbers": phone_numbers}, asset_purchase_phone_numbers_params.AssetPurchasePhoneNumbersParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def purchase_whatsapp_sender(
        self,
        *,
        phone_number: str,
        profile: asset_purchase_whatsapp_sender_params.Profile,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Purchase a phone number and register it as a WhatsApp sender.

        Args:
          phone_number: Phone number in E.164 format.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/api/team/assets/purchase_whatsapp_sender",
            body=await async_maybe_transform(
                {
                    "phone_number": phone_number,
                    "profile": profile,
                },
                asset_purchase_whatsapp_sender_params.AssetPurchaseWhatsappSenderParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def register_phone_number(
        self,
        *,
        integration_id: str,
        phone_number: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AssetRegisterPhoneNumberResponse:
        """
        Register a phone number for the team via Twilio integration.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/team/assets/register_phone_number",
            body=await async_maybe_transform(
                {
                    "integration_id": integration_id,
                    "phone_number": phone_number,
                },
                asset_register_phone_number_params.AssetRegisterPhoneNumberParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AssetRegisterPhoneNumberResponse,
        )

    async def retrieve_whatsapp_sender_status(
        self,
        sender_sid: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Get the status of a WhatsApp sender.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not sender_sid:
            raise ValueError(f"Expected a non-empty value for `sender_sid` but received {sender_sid!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._get(
            f"/api/team/assets/whatsapp_sender_status/{sender_sid}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AssetsResourceWithRawResponse:
    def __init__(self, assets: AssetsResource) -> None:
        self._assets = assets

        self.delete_phone_number = to_raw_response_wrapper(
            assets.delete_phone_number,
        )
        self.list_available_phone_numbers = to_raw_response_wrapper(
            assets.list_available_phone_numbers,
        )
        self.list_phone_numbers = to_raw_response_wrapper(
            assets.list_phone_numbers,
        )
        self.purchase_phone_numbers = to_raw_response_wrapper(
            assets.purchase_phone_numbers,
        )
        self.purchase_whatsapp_sender = to_raw_response_wrapper(
            assets.purchase_whatsapp_sender,
        )
        self.register_phone_number = to_raw_response_wrapper(
            assets.register_phone_number,
        )
        self.retrieve_whatsapp_sender_status = to_raw_response_wrapper(
            assets.retrieve_whatsapp_sender_status,
        )


class AsyncAssetsResourceWithRawResponse:
    def __init__(self, assets: AsyncAssetsResource) -> None:
        self._assets = assets

        self.delete_phone_number = async_to_raw_response_wrapper(
            assets.delete_phone_number,
        )
        self.list_available_phone_numbers = async_to_raw_response_wrapper(
            assets.list_available_phone_numbers,
        )
        self.list_phone_numbers = async_to_raw_response_wrapper(
            assets.list_phone_numbers,
        )
        self.purchase_phone_numbers = async_to_raw_response_wrapper(
            assets.purchase_phone_numbers,
        )
        self.purchase_whatsapp_sender = async_to_raw_response_wrapper(
            assets.purchase_whatsapp_sender,
        )
        self.register_phone_number = async_to_raw_response_wrapper(
            assets.register_phone_number,
        )
        self.retrieve_whatsapp_sender_status = async_to_raw_response_wrapper(
            assets.retrieve_whatsapp_sender_status,
        )


class AssetsResourceWithStreamingResponse:
    def __init__(self, assets: AssetsResource) -> None:
        self._assets = assets

        self.delete_phone_number = to_streamed_response_wrapper(
            assets.delete_phone_number,
        )
        self.list_available_phone_numbers = to_streamed_response_wrapper(
            assets.list_available_phone_numbers,
        )
        self.list_phone_numbers = to_streamed_response_wrapper(
            assets.list_phone_numbers,
        )
        self.purchase_phone_numbers = to_streamed_response_wrapper(
            assets.purchase_phone_numbers,
        )
        self.purchase_whatsapp_sender = to_streamed_response_wrapper(
            assets.purchase_whatsapp_sender,
        )
        self.register_phone_number = to_streamed_response_wrapper(
            assets.register_phone_number,
        )
        self.retrieve_whatsapp_sender_status = to_streamed_response_wrapper(
            assets.retrieve_whatsapp_sender_status,
        )


class AsyncAssetsResourceWithStreamingResponse:
    def __init__(self, assets: AsyncAssetsResource) -> None:
        self._assets = assets

        self.delete_phone_number = async_to_streamed_response_wrapper(
            assets.delete_phone_number,
        )
        self.list_available_phone_numbers = async_to_streamed_response_wrapper(
            assets.list_available_phone_numbers,
        )
        self.list_phone_numbers = async_to_streamed_response_wrapper(
            assets.list_phone_numbers,
        )
        self.purchase_phone_numbers = async_to_streamed_response_wrapper(
            assets.purchase_phone_numbers,
        )
        self.purchase_whatsapp_sender = async_to_streamed_response_wrapper(
            assets.purchase_whatsapp_sender,
        )
        self.register_phone_number = async_to_streamed_response_wrapper(
            assets.register_phone_number,
        )
        self.retrieve_whatsapp_sender_status = async_to_streamed_response_wrapper(
            assets.retrieve_whatsapp_sender_status,
        )

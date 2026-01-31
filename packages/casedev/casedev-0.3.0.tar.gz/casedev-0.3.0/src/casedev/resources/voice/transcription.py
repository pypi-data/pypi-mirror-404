# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...types.voice import transcription_create_params
from ..._base_client import make_request_options
from ...types.voice.transcription_create_response import TranscriptionCreateResponse
from ...types.voice.transcription_retrieve_response import TranscriptionRetrieveResponse

__all__ = ["TranscriptionResource", "AsyncTranscriptionResource"]


class TranscriptionResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> TranscriptionResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/CaseMark/casedev-python#accessing-raw-response-data-eg-headers
        """
        return TranscriptionResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TranscriptionResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/CaseMark/casedev-python#with_streaming_response
        """
        return TranscriptionResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        audio_url: str | Omit = omit,
        auto_highlights: bool | Omit = omit,
        boost_param: Literal["low", "default", "high"] | Omit = omit,
        content_safety_labels: bool | Omit = omit,
        format: Literal["json", "text"] | Omit = omit,
        format_text: bool | Omit = omit,
        language_code: str | Omit = omit,
        language_detection: bool | Omit = omit,
        object_id: str | Omit = omit,
        punctuate: bool | Omit = omit,
        speaker_labels: bool | Omit = omit,
        speakers_expected: int | Omit = omit,
        vault_id: str | Omit = omit,
        word_boost: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TranscriptionCreateResponse:
        """Creates an asynchronous transcription job for audio files.

        Supports two modes:

        **Vault-based (recommended)**: Pass `vault_id` and `object_id` to transcribe
        audio from your vault. The transcript will automatically be saved back to the
        vault when complete.

        **Direct URL (legacy)**: Pass `audio_url` for direct transcription without
        automatic storage.

        Args:
          audio_url: URL of the audio file to transcribe (legacy mode, no auto-storage)

          auto_highlights: Automatically extract key phrases and topics

          boost_param: How much to boost custom vocabulary

          content_safety_labels: Enable content moderation and safety labeling

          format: Output format for the transcript when using vault mode

          format_text: Format text with proper capitalization

          language_code: Language code (e.g., 'en_us', 'es', 'fr'). If not specified, language will be
              auto-detected

          language_detection: Enable automatic language detection

          object_id: Object ID of the audio file in the vault (use with vault_id)

          punctuate: Add punctuation to the transcript

          speaker_labels: Enable speaker identification and labeling

          speakers_expected: Expected number of speakers (improves accuracy when known)

          vault_id: Vault ID containing the audio file (use with object_id)

          word_boost: Custom vocabulary words to boost (e.g., legal terms)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/voice/transcription",
            body=maybe_transform(
                {
                    "audio_url": audio_url,
                    "auto_highlights": auto_highlights,
                    "boost_param": boost_param,
                    "content_safety_labels": content_safety_labels,
                    "format": format,
                    "format_text": format_text,
                    "language_code": language_code,
                    "language_detection": language_detection,
                    "object_id": object_id,
                    "punctuate": punctuate,
                    "speaker_labels": speaker_labels,
                    "speakers_expected": speakers_expected,
                    "vault_id": vault_id,
                    "word_boost": word_boost,
                },
                transcription_create_params.TranscriptionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TranscriptionCreateResponse,
        )

    def retrieve(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TranscriptionRetrieveResponse:
        """Retrieve the status and result of an audio transcription job.

        For vault-based
        jobs, returns status and result_object_id when complete. For legacy direct URL
        jobs, returns the full transcription data.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/voice/transcription/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TranscriptionRetrieveResponse,
        )


class AsyncTranscriptionResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncTranscriptionResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/CaseMark/casedev-python#accessing-raw-response-data-eg-headers
        """
        return AsyncTranscriptionResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTranscriptionResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/CaseMark/casedev-python#with_streaming_response
        """
        return AsyncTranscriptionResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        audio_url: str | Omit = omit,
        auto_highlights: bool | Omit = omit,
        boost_param: Literal["low", "default", "high"] | Omit = omit,
        content_safety_labels: bool | Omit = omit,
        format: Literal["json", "text"] | Omit = omit,
        format_text: bool | Omit = omit,
        language_code: str | Omit = omit,
        language_detection: bool | Omit = omit,
        object_id: str | Omit = omit,
        punctuate: bool | Omit = omit,
        speaker_labels: bool | Omit = omit,
        speakers_expected: int | Omit = omit,
        vault_id: str | Omit = omit,
        word_boost: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TranscriptionCreateResponse:
        """Creates an asynchronous transcription job for audio files.

        Supports two modes:

        **Vault-based (recommended)**: Pass `vault_id` and `object_id` to transcribe
        audio from your vault. The transcript will automatically be saved back to the
        vault when complete.

        **Direct URL (legacy)**: Pass `audio_url` for direct transcription without
        automatic storage.

        Args:
          audio_url: URL of the audio file to transcribe (legacy mode, no auto-storage)

          auto_highlights: Automatically extract key phrases and topics

          boost_param: How much to boost custom vocabulary

          content_safety_labels: Enable content moderation and safety labeling

          format: Output format for the transcript when using vault mode

          format_text: Format text with proper capitalization

          language_code: Language code (e.g., 'en_us', 'es', 'fr'). If not specified, language will be
              auto-detected

          language_detection: Enable automatic language detection

          object_id: Object ID of the audio file in the vault (use with vault_id)

          punctuate: Add punctuation to the transcript

          speaker_labels: Enable speaker identification and labeling

          speakers_expected: Expected number of speakers (improves accuracy when known)

          vault_id: Vault ID containing the audio file (use with object_id)

          word_boost: Custom vocabulary words to boost (e.g., legal terms)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/voice/transcription",
            body=await async_maybe_transform(
                {
                    "audio_url": audio_url,
                    "auto_highlights": auto_highlights,
                    "boost_param": boost_param,
                    "content_safety_labels": content_safety_labels,
                    "format": format,
                    "format_text": format_text,
                    "language_code": language_code,
                    "language_detection": language_detection,
                    "object_id": object_id,
                    "punctuate": punctuate,
                    "speaker_labels": speaker_labels,
                    "speakers_expected": speakers_expected,
                    "vault_id": vault_id,
                    "word_boost": word_boost,
                },
                transcription_create_params.TranscriptionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TranscriptionCreateResponse,
        )

    async def retrieve(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TranscriptionRetrieveResponse:
        """Retrieve the status and result of an audio transcription job.

        For vault-based
        jobs, returns status and result_object_id when complete. For legacy direct URL
        jobs, returns the full transcription data.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/voice/transcription/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TranscriptionRetrieveResponse,
        )


class TranscriptionResourceWithRawResponse:
    def __init__(self, transcription: TranscriptionResource) -> None:
        self._transcription = transcription

        self.create = to_raw_response_wrapper(
            transcription.create,
        )
        self.retrieve = to_raw_response_wrapper(
            transcription.retrieve,
        )


class AsyncTranscriptionResourceWithRawResponse:
    def __init__(self, transcription: AsyncTranscriptionResource) -> None:
        self._transcription = transcription

        self.create = async_to_raw_response_wrapper(
            transcription.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            transcription.retrieve,
        )


class TranscriptionResourceWithStreamingResponse:
    def __init__(self, transcription: TranscriptionResource) -> None:
        self._transcription = transcription

        self.create = to_streamed_response_wrapper(
            transcription.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            transcription.retrieve,
        )


class AsyncTranscriptionResourceWithStreamingResponse:
    def __init__(self, transcription: AsyncTranscriptionResource) -> None:
        self._transcription = transcription

        self.create = async_to_streamed_response_wrapper(
            transcription.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            transcription.retrieve,
        )

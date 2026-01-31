# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

from ..._types import SequenceNotStr

__all__ = ["TranscriptionCreateParams"]


class TranscriptionCreateParams(TypedDict, total=False):
    audio_url: str
    """URL of the audio file to transcribe (legacy mode, no auto-storage)"""

    auto_highlights: bool
    """Automatically extract key phrases and topics"""

    boost_param: Literal["low", "default", "high"]
    """How much to boost custom vocabulary"""

    content_safety_labels: bool
    """Enable content moderation and safety labeling"""

    format: Literal["json", "text"]
    """Output format for the transcript when using vault mode"""

    format_text: bool
    """Format text with proper capitalization"""

    language_code: str
    """Language code (e.g., 'en_us', 'es', 'fr').

    If not specified, language will be auto-detected
    """

    language_detection: bool
    """Enable automatic language detection"""

    object_id: str
    """Object ID of the audio file in the vault (use with vault_id)"""

    punctuate: bool
    """Add punctuation to the transcript"""

    speaker_labels: bool
    """Enable speaker identification and labeling"""

    speakers_expected: int
    """Expected number of speakers (improves accuracy when known)"""

    vault_id: str
    """Vault ID containing the audio file (use with object_id)"""

    word_boost: SequenceNotStr[str]
    """Custom vocabulary words to boost (e.g., legal terms)"""

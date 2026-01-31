# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["StreamingGetURLResponse", "AudioFormat", "Pricing"]


class AudioFormat(BaseModel):
    channels: Optional[int] = None
    """Number of audio channels"""

    encoding: Optional[str] = None
    """Required audio encoding format"""

    sample_rate: Optional[int] = None
    """Required audio sample rate in Hz"""


class Pricing(BaseModel):
    currency: Optional[str] = None
    """Currency for pricing"""

    per_hour: Optional[float] = None
    """Cost per hour of transcription"""

    per_minute: Optional[float] = None
    """Cost per minute of transcription"""


class StreamingGetURLResponse(BaseModel):
    audio_format: Optional[AudioFormat] = None

    connect_url: Optional[str] = None
    """Complete WebSocket URL with authentication token"""

    pricing: Optional[Pricing] = None

    protocol: Optional[str] = None
    """Connection protocol"""

    url: Optional[str] = None
    """Base WebSocket URL for streaming transcription"""

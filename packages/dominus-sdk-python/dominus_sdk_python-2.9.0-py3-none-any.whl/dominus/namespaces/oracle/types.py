"""
Oracle Namespace Types - Public interfaces for streaming transcription.

Oracle provides real-time speech-to-text via Deepgram streaming,
with built-in VAD (Voice Activity Detection) for cost optimization.
"""

from typing import Literal, Optional, Callable, TypedDict
from dataclasses import dataclass, field


# VAD (Voice Activity Detection) states
VADState = Literal["idle", "armed", "speaking", "trailing"]


@dataclass
class OracleSessionOptions:
    """Configuration options for OracleSession."""

    # Pre-roll buffer duration in ms (default: 320)
    preroll_ms: int = 320

    # Post-roll duration in ms (default: 800)
    postroll_ms: int = 800

    # VAD confirmation time in ms (default: 160)
    armed_confirm_ms: int = 160

    # VAD speech threshold 0-1 (default: 0.5) - used for energy-based fallback
    vad_threshold: float = 0.5

    # Energy threshold for fallback VAD (default: 800)
    energy_threshold: int = 800

    # Ping interval in ms for keepalive (default: 10000)
    ping_interval_ms: int = 10000


@dataclass
class ResolvedOracleSessionOptions:
    """Resolved session options with all defaults applied."""

    preroll_ms: int
    postroll_ms: int
    armed_confirm_ms: int
    vad_threshold: float
    energy_threshold: int
    ping_interval_ms: int


# Default configuration values
DEFAULT_OPTIONS = ResolvedOracleSessionOptions(
    preroll_ms=320,           # 16 frames x 20ms
    postroll_ms=800,          # Post-roll trailing duration
    armed_confirm_ms=160,     # 8 frames x 20ms to confirm speech
    vad_threshold=0.5,        # VAD threshold
    energy_threshold=800,     # Energy-based fallback threshold
    ping_interval_ms=10000,   # 10 second ping interval
)


@dataclass
class AudioConfig:
    """Audio configuration constants."""

    SAMPLE_RATE: int = 16000       # 16kHz
    CHANNELS: int = 1               # Mono
    FRAME_DURATION_MS: int = 20     # 20ms frames
    FRAME_SIZE_BYTES: int = 640     # 320 samples x 2 bytes per sample
    SAMPLES_PER_FRAME: int = 320    # 16kHz x 20ms


AUDIO_CONFIG = AudioConfig()


class ServerReadyMessage(TypedDict):
    """Server ready message."""
    type: Literal["ready"]


class ServerTranscriptMessage(TypedDict):
    """Server transcript message."""
    type: Literal["transcript"]
    text: str
    is_final: bool
    speech_final: bool


class ServerPongMessage(TypedDict):
    """Server pong message."""
    type: Literal["pong"]


class ServerErrorMessage(TypedDict):
    """Server error message."""
    type: Literal["error"]
    message: str


# Union type for server messages
ServerMessage = ServerReadyMessage | ServerTranscriptMessage | ServerPongMessage | ServerErrorMessage


@dataclass
class OracleSessionCallbacks:
    """Event callbacks for OracleSession."""

    # Called when session is ready to receive speech
    on_ready: Optional[Callable[[], None]] = None

    # Called with interim transcripts (may change)
    on_interim: Optional[Callable[[str], None]] = None

    # Called when a transcript segment is finalized
    on_final: Optional[Callable[[str], None]] = None

    # Called when user finishes an utterance (trigger for Curator)
    on_utterance: Optional[Callable[[str], None]] = None

    # Called on any error
    on_error: Optional[Callable[[Exception], None]] = None

    # Called when session closes
    on_close: Optional[Callable[[], None]] = None

    # Called when VAD state changes (for UI indicators)
    on_vad_state_change: Optional[Callable[[VADState], None]] = None

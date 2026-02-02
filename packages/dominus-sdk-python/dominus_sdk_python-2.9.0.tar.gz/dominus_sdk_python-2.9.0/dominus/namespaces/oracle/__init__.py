"""
Oracle Namespace - Real-time streaming speech-to-text.

Provides WebSocket-based streaming transcription via Deepgram,
with built-in VAD (Voice Activity Detection) for cost optimization.

Key features:
- Automatic microphone capture and 16kHz resampling
- VAD gating: only sends audio when speech is detected
- 4-state VAD machine: IDLE -> ARMED -> SPEAKING -> TRAILING
- Pre-roll buffer captures word onsets
- Ping/pong keepalive during IDLE
- NO send_audio() exposed - VAD handles everything

Usage:
    session = dominus.oracle.create_session(user_jwt)

    session.on_ready = lambda: set_listening(True)
    session.on_interim = lambda text: set_live_transcript(text)
    session.on_utterance = lambda text: send_to_curator(text)
    session.on_vad_state_change = lambda state: set_mic_state(state)
    session.on_error = lambda error: show_error(error)

    await session.start()
    # ... user speaks, transcripts flow back ...
    await session.stop()
"""

from typing import Optional, TYPE_CHECKING

from .types import (
    VADState,
    OracleSessionOptions,
    ResolvedOracleSessionOptions,
    DEFAULT_OPTIONS,
    AUDIO_CONFIG,
)
from .session import OracleSession

if TYPE_CHECKING:
    from ...start import Dominus

# Re-export public types
__all__ = [
    "OracleNamespace",
    "OracleSession",
    "OracleSessionOptions",
    "VADState",
]


class OracleNamespace:
    """
    OracleNamespace - Factory for creating streaming transcription sessions.

    The Oracle namespace provides a simple API for real-time speech-to-text:
    - create_session() creates a new transcription session
    - Sessions handle mic capture, VAD, WebSocket, and transcripts internally
    - NO raw audio access - VAD is mandatory for cost control
    """

    def __init__(self, client: "Dominus"):
        from ...config.endpoints import BASE_URL
        self._base_url = BASE_URL
        self._client = client

    def create_session(
        self,
        user_token: str,
        options: Optional[OracleSessionOptions] = None
    ) -> OracleSession:
        """
        Create a streaming transcription session.

        The session handles everything internally:
        - Microphone access and audio capture
        - Resampling to 16kHz mono PCM
        - VAD gating (only sends speech, not silence)
        - WebSocket connection to Oracle
        - Reconnection on connection loss

        Args:
            user_token: User JWT from portal.login()
            options: Optional configuration overrides

        Returns:
            OracleSession ready to start()

        Example:
            session = dominus.oracle.create_session(user_jwt, OracleSessionOptions(
                preroll_ms=320,      # Capture 320ms before speech
                postroll_ms=400,     # Continue 400ms after speech
                armed_confirm_ms=80, # Require 80ms to confirm speech
            ))

            session.on_utterance = lambda text: send_to_curator(text)

            await session.start()
        """
        # Merge options with defaults
        if options:
            resolved_options = ResolvedOracleSessionOptions(
                preroll_ms=options.preroll_ms if options.preroll_ms != DEFAULT_OPTIONS.preroll_ms else DEFAULT_OPTIONS.preroll_ms,
                postroll_ms=options.postroll_ms if options.postroll_ms != DEFAULT_OPTIONS.postroll_ms else DEFAULT_OPTIONS.postroll_ms,
                armed_confirm_ms=options.armed_confirm_ms if options.armed_confirm_ms != DEFAULT_OPTIONS.armed_confirm_ms else DEFAULT_OPTIONS.armed_confirm_ms,
                vad_threshold=options.vad_threshold if options.vad_threshold != DEFAULT_OPTIONS.vad_threshold else DEFAULT_OPTIONS.vad_threshold,
                energy_threshold=options.energy_threshold if options.energy_threshold != DEFAULT_OPTIONS.energy_threshold else DEFAULT_OPTIONS.energy_threshold,
                ping_interval_ms=options.ping_interval_ms if options.ping_interval_ms != DEFAULT_OPTIONS.ping_interval_ms else DEFAULT_OPTIONS.ping_interval_ms,
            )
        else:
            resolved_options = ResolvedOracleSessionOptions(
                preroll_ms=DEFAULT_OPTIONS.preroll_ms,
                postroll_ms=DEFAULT_OPTIONS.postroll_ms,
                armed_confirm_ms=DEFAULT_OPTIONS.armed_confirm_ms,
                vad_threshold=DEFAULT_OPTIONS.vad_threshold,
                energy_threshold=DEFAULT_OPTIONS.energy_threshold,
                ping_interval_ms=DEFAULT_OPTIONS.ping_interval_ms,
            )

        return OracleSession(self._base_url, user_token, resolved_options)

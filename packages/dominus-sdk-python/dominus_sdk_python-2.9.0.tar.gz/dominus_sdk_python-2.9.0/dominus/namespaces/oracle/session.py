"""
OracleSession - Main session class for streaming transcription.

Provides the public API for Oracle streaming:
- start() / stop() lifecycle
- Event callbacks for transcripts, VAD state, errors
- NO send_audio() exposed - VAD gates all audio automatically

The session handles everything internally:
- Microphone access and audio capture
- Resampling to 16kHz mono PCM
- VAD gating (only sends speech, not silence)
- WebSocket connection to Oracle
- Ping/pong keepalive during IDLE
"""

import asyncio
from typing import Callable, Optional, List

from .oracle_websocket import OracleWebSocket, OracleWebSocketConfig
from .vad_gate import VADGate
from .audio_capture import AudioCapture
from .types import VADState, ResolvedOracleSessionOptions


class OracleSession:
    """
    OracleSession - Real-time speech-to-text with VAD gating.

    Usage:
        session = dominus.oracle.create_session(user_jwt)

        session.on_ready = lambda: print('Ready')
        session.on_interim = lambda text: set_live_text(text)
        session.on_utterance = lambda text: send_to_curator(text)
        session.on_vad_state_change = lambda state: update_mic_icon(state)

        await session.start()
        # ... user speaks ...
        await session.stop()
    """

    def __init__(
        self,
        base_url: str,
        user_token: str,
        options: ResolvedOracleSessionOptions
    ):
        self._user_token = user_token
        self._is_active = False
        self._vad_state: VADState = "idle"

        # Track accumulated transcript for utterance detection
        # Since VAD stops sending audio before Deepgram's utterance_end_ms,
        # we use VAD TRAILING->IDLE transition as utterance boundary
        self._pending_utterance = ""

        # Initialize internal components
        self._ws = OracleWebSocket(
            base_url,
            OracleWebSocketConfig(ping_interval_ms=options.ping_interval_ms)
        )
        self._vad = VADGate(options)
        self._audio = AudioCapture()

        # ========== EVENT CALLBACKS ==========

        # Called when session is ready to receive speech
        self.on_ready: Optional[Callable[[], None]] = None

        # Called with interim transcripts (may change)
        self.on_interim: Optional[Callable[[str], None]] = None

        # Called when a transcript segment is finalized
        self.on_final: Optional[Callable[[str], None]] = None

        # Called when user finishes an utterance (trigger for Curator)
        self.on_utterance: Optional[Callable[[str], None]] = None

        # Called on any error
        self.on_error: Optional[Callable[[Exception], None]] = None

        # Called when session closes
        self.on_close: Optional[Callable[[], None]] = None

        # Called when VAD state changes (for UI indicators)
        self.on_vad_state_change: Optional[Callable[[VADState], None]] = None

    # ========== PUBLIC GETTERS ==========

    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self._is_active

    @property
    def vad_state(self) -> VADState:
        """Get current VAD state."""
        return self._vad_state

    # ========== LIFECYCLE METHODS ==========

    async def start(self) -> None:
        """
        Start the transcription session.

        - Requests microphone permission
        - Connects WebSocket to Oracle
        - Begins VAD-gated audio streaming

        Raises:
            Exception: If mic permission denied or connection fails
        """
        if self._is_active:
            return

        try:
            # 1. Initialize VAD
            await self._vad.initialize()

            # 2. Connect WebSocket with first-message auth
            await self._ws.connect(self._user_token)

            # 3. Wire up transcript events
            def on_transcript(text: str, is_final: bool, speech_final: bool):
                if not is_final:
                    # Interim: show in live view (may change)
                    if self.on_interim:
                        self.on_interim(text)
                else:
                    # Final: accumulate for utterance
                    if self.on_final:
                        self.on_final(text)
                    # Accumulate finals - space-separated
                    if self._pending_utterance:
                        self._pending_utterance += " " + text
                    else:
                        self._pending_utterance = text

                # If Deepgram does send speech_final, honor it
                if speech_final and text:
                    self._pending_utterance = ""  # Clear since we're emitting
                    if self.on_utterance:
                        self.on_utterance(text)

            self._ws.on_transcript = on_transcript

            self._ws.on_error = lambda error: (
                self.on_error(error) if self.on_error else None
            )

            def on_ws_close():
                self._is_active = False
                if self.on_close:
                    self.on_close()

            self._ws.on_close = on_ws_close

            # 4. Start audio capture
            await self._audio.start()

            # 5. Wire audio through VAD gate
            def on_audio_frame(pcm_frame: bytes):
                self._vad.process_frame(pcm_frame)

            self._audio.on_frame = on_audio_frame

            # 6. VAD gate controls what gets sent
            def on_send_audio(frames: List[bytes]):
                for frame in frames:
                    self._ws.send_binary(frame)

            self._vad.on_send_audio = on_send_audio

            def on_vad_state_change(state: VADState):
                prev_state = self._vad_state
                self._vad_state = state

                if self.on_vad_state_change:
                    self.on_vad_state_change(state)

                # When VAD transitions to IDLE from TRAILING, emit accumulated utterance
                if state == "idle" and (prev_state == "trailing" or prev_state == "speaking"):
                    if self._pending_utterance.strip():
                        print(f"[OracleSDK] VAD->IDLE: emitting utterance: "
                              f"{self._pending_utterance[:50]!r}")
                        if self.on_utterance:
                            self.on_utterance(self._pending_utterance.strip())
                        self._pending_utterance = ""

            self._vad.on_state_change = on_vad_state_change

            self._is_active = True

            if self.on_ready:
                self.on_ready()

        except Exception as e:
            # Clean up on failure
            await self._cleanup()
            raise e

    async def stop(self) -> None:
        """
        Stop the transcription session.

        - Stops microphone capture
        - Closes WebSocket connection
        - Cleans up resources
        """
        if not self._is_active:
            return

        self._is_active = False
        await self._cleanup()

        if self.on_close:
            self.on_close()

    # ========== PRIVATE METHODS ==========

    async def _cleanup(self) -> None:
        """Clean up all resources."""
        # Stop audio capture
        await self._audio.stop()

        # Close WebSocket
        await self._ws.close()

        # Reset VAD state
        self._vad.reset()
        self._vad_state = "idle"

        # Clear pending utterance
        self._pending_utterance = ""

    def dispose(self) -> None:
        """Dispose of all resources (for cleanup on unmount)."""
        asyncio.create_task(self.stop())

        # Clear all callbacks
        self.on_ready = None
        self.on_interim = None
        self.on_final = None
        self.on_utterance = None
        self.on_error = None
        self.on_close = None
        self.on_vad_state_change = None

        # Dispose internal components
        self._audio.dispose()
        self._vad.dispose()

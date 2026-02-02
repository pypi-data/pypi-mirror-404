"""
VADGate - Voice Activity Detection Gate (INTERNAL)

Implements a 4-state machine for VAD gating:
IDLE -> ARMED -> SPEAKING -> TRAILING -> IDLE

Features:
- Pre-roll buffer (320ms) to capture word onsets
- Armed confirmation (160ms) to reject false triggers
- Post-roll/trailing (800ms) to avoid chopped endings
- Circular buffer for pre-roll storage

This module is INTERNAL and should NOT be exported publicly.
"""

import asyncio
import struct
import math
from typing import List, Callable, Optional
from dataclasses import dataclass

from .types import VADState, ResolvedOracleSessionOptions


@dataclass
class VADGateConfig:
    """Configuration for VADGate."""

    # Number of frames in pre-roll buffer
    preroll_frames: int

    # Number of frames to confirm armed state
    armed_confirm_frames: int

    # Number of consecutive silence frames to confirm trailing (hysteresis)
    silence_confirm_frames: int

    # Post-roll timeout in ms
    postroll_ms: int

    # VAD threshold (0-1)
    threshold: float

    # Energy threshold for fallback VAD
    energy_threshold: int


def detect_speech_by_energy(pcm_frame: bytes, threshold: int = 500) -> bool:
    """
    Energy-based speech detection fallback.
    Calculates RMS energy and compares against threshold.

    Args:
        pcm_frame: Raw PCM16 audio data
        threshold: RMS energy threshold

    Returns:
        True if speech detected, False otherwise
    """
    # Convert bytes to int16 samples
    num_samples = len(pcm_frame) // 2
    if num_samples == 0:
        return False

    samples = struct.unpack(f"<{num_samples}h", pcm_frame)

    # Calculate RMS energy
    sum_squares = sum(s * s for s in samples)
    rms = math.sqrt(sum_squares / num_samples)

    return rms > threshold


class EnergyVAD:
    """
    Energy-based VAD fallback.
    Uses RMS energy detection when webrtcvad is unavailable.
    """

    def __init__(self, energy_threshold: int):
        self.energy_threshold = energy_threshold

    def is_speech(self, pcm_frame: bytes, _threshold: float) -> bool:
        return detect_speech_by_energy(pcm_frame, self.energy_threshold)

    def dispose(self) -> None:
        pass


class WebRTCVAD:
    """
    WebRTC VAD wrapper.
    Falls back to energy-based detection if webrtcvad is unavailable.
    """

    def __init__(self, threshold: float, energy_threshold: int, sample_rate: int = 16000):
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.fallback = EnergyVAD(energy_threshold)
        self.vad = None
        self.use_fallback = False

        try:
            import webrtcvad
            self.vad = webrtcvad.Vad()
            # Aggressiveness level 0-3 (3 = most aggressive filtering)
            # Map threshold (0-1) to aggressiveness (0-3)
            aggressiveness = max(0, min(3, int((1 - threshold) * 3)))
            self.vad.set_mode(aggressiveness)
        except ImportError:
            print("[OracleSDK] webrtcvad not available, using energy-based fallback")
            self.use_fallback = True

    def is_speech(self, pcm_frame: bytes, threshold: float) -> bool:
        if self.use_fallback or self.vad is None:
            return self.fallback.is_speech(pcm_frame, threshold)

        try:
            # webrtcvad requires specific frame sizes: 10, 20, or 30 ms
            # For 16kHz, 20ms = 320 samples = 640 bytes
            return self.vad.is_speech(pcm_frame, self.sample_rate)
        except Exception:
            # Fall back to energy-based on any error
            return self.fallback.is_speech(pcm_frame, threshold)

    def dispose(self) -> None:
        self.vad = None


class VADGate:
    """
    VADGate - 4-state Voice Activity Detection machine.

    State transitions:
    - IDLE -> ARMED: When VAD detects speech
    - ARMED -> SPEAKING: After armed_confirm_frames of continuous speech
    - ARMED -> IDLE: If speech stops before confirmation
    - SPEAKING -> TRAILING: When VAD detects silence
    - TRAILING -> SPEAKING: If speech resumes
    - TRAILING -> IDLE: After postroll_ms timeout
    """

    def __init__(
        self,
        options: ResolvedOracleSessionOptions,
        frame_duration_ms: int = 20,
        loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        self._state: VADState = "idle"
        self._pre_roll_buffer: List[bytes] = []
        self._armed_frame_count = 0
        self._silence_frame_count = 0
        self._trailing_task: Optional[asyncio.Task] = None
        self._loop = loop

        self._config = VADGateConfig(
            preroll_frames=math.ceil(options.preroll_ms / frame_duration_ms),
            armed_confirm_frames=math.ceil(options.armed_confirm_ms / frame_duration_ms),
            silence_confirm_frames=8,  # 160ms of silence before trailing
            postroll_ms=options.postroll_ms,
            threshold=options.vad_threshold,
            energy_threshold=options.energy_threshold,
        )

        # Use energy-based VAD as the primary implementation
        self._vad_model = EnergyVAD(self._config.energy_threshold)

        # Callbacks
        self.on_send_audio: Optional[Callable[[List[bytes]], None]] = None
        self.on_state_change: Optional[Callable[[VADState], None]] = None

    @property
    def state(self) -> VADState:
        """Get current VAD state."""
        return self._state

    async def initialize(self) -> None:
        """Initialize the VAD model (call before processing frames)."""
        # Energy VAD doesn't need initialization
        pass

    def process_frame(self, pcm_frame: bytes) -> None:
        """
        Process an audio frame through the VAD gate.

        Args:
            pcm_frame: 20ms PCM16 audio frame (640 bytes)
        """
        # Maintain circular pre-roll buffer
        self._pre_roll_buffer.append(pcm_frame)
        if len(self._pre_roll_buffer) > self._config.preroll_frames:
            self._pre_roll_buffer.pop(0)

        is_speech = self._vad_model.is_speech(pcm_frame, self._config.threshold)

        if self._state == "idle":
            if is_speech:
                self._set_state("armed")
                self._armed_frame_count = 1

        elif self._state == "armed":
            if is_speech:
                self._armed_frame_count += 1
                if self._armed_frame_count >= self._config.armed_confirm_frames:
                    # Confirmed speech - flush pre-roll buffer
                    if self.on_send_audio:
                        self.on_send_audio(list(self._pre_roll_buffer))
                    self._set_state("speaking")
            else:
                # False trigger - back to idle
                self._set_state("idle")
                self._armed_frame_count = 0

        elif self._state == "speaking":
            if self.on_send_audio:
                self.on_send_audio([pcm_frame])

            if not is_speech:
                # Hysteresis: require multiple consecutive silence frames
                self._silence_frame_count += 1
                if self._silence_frame_count >= self._config.silence_confirm_frames:
                    self._set_state("trailing")
                    self._start_trailing_timer()
                    self._silence_frame_count = 0
            else:
                # Speech detected - reset silence counter
                self._silence_frame_count = 0

        elif self._state == "trailing":
            if self.on_send_audio:
                self.on_send_audio([pcm_frame])

            if is_speech:
                self._cancel_trailing_timer()
                self._set_state("speaking")

    def reset(self) -> None:
        """Reset VAD state to idle."""
        self._cancel_trailing_timer()
        self._state = "idle"
        self._pre_roll_buffer = []
        self._armed_frame_count = 0
        self._silence_frame_count = 0

    def dispose(self) -> None:
        """Clean up resources."""
        self._cancel_trailing_timer()
        self._vad_model.dispose()
        self.on_send_audio = None
        self.on_state_change = None

    def _set_state(self, new_state: VADState) -> None:
        """Update VAD state and fire callback."""
        if self._state != new_state:
            self._state = new_state
            if self.on_state_change:
                self.on_state_change(new_state)

    def _start_trailing_timer(self) -> None:
        """
        Start the trailing timeout.
        After postroll_ms, transition back to idle.
        """
        async def trailing_timeout():
            await asyncio.sleep(self._config.postroll_ms / 1000.0)
            self._set_state("idle")
            self._trailing_task = None

        loop = self._loop or asyncio.get_event_loop()
        self._trailing_task = loop.create_task(trailing_timeout())

    def _cancel_trailing_timer(self) -> None:
        """Cancel the trailing timeout."""
        if self._trailing_task is not None:
            self._trailing_task.cancel()
            self._trailing_task = None

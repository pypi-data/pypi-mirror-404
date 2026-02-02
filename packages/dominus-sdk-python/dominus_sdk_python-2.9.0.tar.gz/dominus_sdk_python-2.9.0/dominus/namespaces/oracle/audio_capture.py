"""
AudioCapture - Microphone capture and resampling (INTERNAL)

Handles:
- Microphone access via sounddevice or pyaudio
- Resampling to 16kHz mono if needed
- Output 20ms frames (640 bytes PCM16)

This module is INTERNAL and should NOT be exported publicly.
"""

import asyncio
import struct
import math
from typing import Callable, Optional, List
from dataclasses import dataclass

from .types import AUDIO_CONFIG

# Try to import audio libraries
try:
    import sounddevice as sd
    import numpy as np
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    sd = None
    np = None

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None


def resample(input_data: List[float], from_rate: int, to_rate: int) -> List[float]:
    """
    Resample audio data using linear interpolation.

    Args:
        input_data: Input samples as floats
        from_rate: Source sample rate
        to_rate: Target sample rate

    Returns:
        Resampled audio data
    """
    if from_rate == to_rate:
        return input_data

    ratio = from_rate / to_rate
    output_length = math.ceil(len(input_data) / ratio)
    output = []

    for i in range(output_length):
        src_index = i * ratio
        src_floor = int(src_index)
        src_ceil = min(src_floor + 1, len(input_data) - 1)
        t = src_index - src_floor

        # Linear interpolation
        value = input_data[src_floor] * (1 - t) + input_data[src_ceil] * t
        output.append(value)

    return output


def float_to_pcm16(samples: List[float]) -> bytes:
    """
    Convert float samples [-1, 1] to PCM16 bytes.

    Args:
        samples: Float samples in range [-1, 1]

    Returns:
        PCM16 bytes (little-endian)
    """
    pcm_values = []
    for s in samples:
        # Clamp to [-1, 1]
        s = max(-1.0, min(1.0, s))
        # Convert to int16
        if s < 0:
            pcm_values.append(int(s * 0x8000))
        else:
            pcm_values.append(int(s * 0x7FFF))

    return struct.pack(f"<{len(pcm_values)}h", *pcm_values)


class SoundDeviceCapture:
    """
    Audio capture using sounddevice library.
    Preferred for cross-platform compatibility.
    """

    def __init__(self):
        if not SOUNDDEVICE_AVAILABLE:
            raise ImportError(
                "sounddevice package is required for audio capture. "
                "Install with: pip install sounddevice numpy"
            )

        self._stream: Optional[sd.InputStream] = None
        self._buffer: List[float] = []
        self._is_capturing = False
        self._callback_queue: asyncio.Queue = None
        self._process_task: Optional[asyncio.Task] = None

        self.on_frame: Optional[Callable[[bytes], None]] = None

    async def start(self) -> None:
        """Start audio capture from microphone."""
        if self._is_capturing:
            return

        self._callback_queue = asyncio.Queue()

        def audio_callback(indata, frames, time_info, status):
            if status:
                print(f"[OracleSDK] Audio status: {status}")

            # Convert numpy array to list of floats
            mono_data = indata[:, 0].tolist() if indata.ndim > 1 else indata.flatten().tolist()

            # Put data in queue for async processing
            try:
                self._callback_queue.put_nowait(mono_data)
            except asyncio.QueueFull:
                pass  # Drop frames if queue is full

        # Open stream
        self._stream = sd.InputStream(
            samplerate=AUDIO_CONFIG.SAMPLE_RATE,
            channels=AUDIO_CONFIG.CHANNELS,
            dtype='float32',
            blocksize=1024,  # Good balance of latency vs efficiency
            callback=audio_callback,
        )
        self._stream.start()
        self._is_capturing = True

        # Start processing task
        self._process_task = asyncio.create_task(self._process_audio())

    async def stop(self) -> None:
        """Stop audio capture."""
        if not self._is_capturing:
            return

        self._is_capturing = False

        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
            self._process_task = None

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self._buffer = []

    async def _process_audio(self) -> None:
        """Process audio from queue and emit frames."""
        while self._is_capturing:
            try:
                # Get audio data from queue
                audio_data = await asyncio.wait_for(
                    self._callback_queue.get(),
                    timeout=0.1
                )

                # Append to buffer
                self._buffer.extend(audio_data)

                # Extract complete frames
                while len(self._buffer) >= AUDIO_CONFIG.SAMPLES_PER_FRAME:
                    frame_samples = self._buffer[:AUDIO_CONFIG.SAMPLES_PER_FRAME]
                    self._buffer = self._buffer[AUDIO_CONFIG.SAMPLES_PER_FRAME:]

                    # Convert to PCM16
                    pcm_frame = float_to_pcm16(frame_samples)

                    if self.on_frame:
                        self.on_frame(pcm_frame)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break


class PyAudioCapture:
    """
    Audio capture using PyAudio library.
    Fallback for environments where sounddevice doesn't work.
    """

    def __init__(self):
        if not PYAUDIO_AVAILABLE:
            raise ImportError(
                "pyaudio package is required for audio capture. "
                "Install with: pip install pyaudio"
            )

        self._pa: Optional[pyaudio.PyAudio] = None
        self._stream = None
        self._buffer: List[float] = []
        self._is_capturing = False
        self._callback_queue: asyncio.Queue = None
        self._process_task: Optional[asyncio.Task] = None

        self.on_frame: Optional[Callable[[bytes], None]] = None

    async def start(self) -> None:
        """Start audio capture from microphone."""
        if self._is_capturing:
            return

        self._pa = pyaudio.PyAudio()
        self._callback_queue = asyncio.Queue()

        def audio_callback(in_data, frame_count, time_info, status):
            # Convert bytes to float samples
            num_samples = len(in_data) // 2
            samples = struct.unpack(f"<{num_samples}h", in_data)
            # Normalize to [-1, 1]
            float_samples = [s / 32768.0 for s in samples]

            try:
                self._callback_queue.put_nowait(float_samples)
            except asyncio.QueueFull:
                pass

            return (None, pyaudio.paContinue)

        # Open stream
        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=AUDIO_CONFIG.CHANNELS,
            rate=AUDIO_CONFIG.SAMPLE_RATE,
            input=True,
            frames_per_buffer=1024,
            stream_callback=audio_callback,
        )
        self._stream.start_stream()
        self._is_capturing = True

        # Start processing task
        self._process_task = asyncio.create_task(self._process_audio())

    async def stop(self) -> None:
        """Stop audio capture."""
        if not self._is_capturing:
            return

        self._is_capturing = False

        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
            self._process_task = None

        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

        if self._pa:
            self._pa.terminate()
            self._pa = None

        self._buffer = []

    async def _process_audio(self) -> None:
        """Process audio from queue and emit frames."""
        while self._is_capturing:
            try:
                audio_data = await asyncio.wait_for(
                    self._callback_queue.get(),
                    timeout=0.1
                )

                self._buffer.extend(audio_data)

                while len(self._buffer) >= AUDIO_CONFIG.SAMPLES_PER_FRAME:
                    frame_samples = self._buffer[:AUDIO_CONFIG.SAMPLES_PER_FRAME]
                    self._buffer = self._buffer[AUDIO_CONFIG.SAMPLES_PER_FRAME:]

                    pcm_frame = float_to_pcm16(frame_samples)

                    if self.on_frame:
                        self.on_frame(pcm_frame)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break


class AudioCapture:
    """
    AudioCapture - Main class for microphone capture.

    Automatically uses sounddevice if available, falls back to PyAudio.
    Outputs 20ms frames (640 bytes PCM16) at 16kHz mono.
    """

    def __init__(self):
        self._capture = None
        self._is_capturing = False

        # Callback for each audio frame
        self.on_frame: Optional[Callable[[bytes], None]] = None

    @property
    def is_capturing(self) -> bool:
        """Check if currently capturing audio."""
        return self._is_capturing

    async def start(self) -> None:
        """
        Start audio capture from microphone.

        Raises:
            ImportError: If no audio library is available
            Exception: If microphone access fails
        """
        if self._is_capturing:
            return

        # Choose capture method based on available libraries
        if SOUNDDEVICE_AVAILABLE:
            try:
                self._capture = SoundDeviceCapture()
                await self._capture.start()
            except Exception as e:
                print(f"[OracleSDK] sounddevice failed, trying PyAudio: {e}")
                if PYAUDIO_AVAILABLE:
                    self._capture = PyAudioCapture()
                    await self._capture.start()
                else:
                    raise
        elif PYAUDIO_AVAILABLE:
            self._capture = PyAudioCapture()
            await self._capture.start()
        else:
            raise ImportError(
                "Audio capture requires either sounddevice or pyaudio. "
                "Install with: pip install sounddevice numpy  OR  pip install pyaudio"
            )

        # Wire up frame callback
        self._capture.on_frame = lambda pcm_frame: (
            self.on_frame(pcm_frame) if self.on_frame else None
        )

        self._is_capturing = True

    async def stop(self) -> None:
        """Stop audio capture."""
        if not self._is_capturing or not self._capture:
            return

        await self._capture.stop()
        self._capture = None
        self._is_capturing = False

    def dispose(self) -> None:
        """Clean up resources."""
        asyncio.create_task(self.stop())
        self.on_frame = None

# Copyright (c) 2018 Anki, Inc.
# Copyright (c) 2025 Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License in the file LICENSE.txt or at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Support for streaming audio FROM Vector via wirepod.

This module provides real-time audio streaming from Vector's microphone
through wirepod's websocket API. This requires a modified wirepod server
with audio streaming support.

The :class:`AudioStreamClient` class can be used standalone or integrated
with the Robot class for seamless audio access.

Example usage::

    import asyncio
    from anki_vector.audio_stream import AudioStreamClient

    async def main():
        client = AudioStreamClient(host="192.168.1.100", port=8080)

        def on_audio(audio_bytes, device):
            print(f"Received {len(audio_bytes)} bytes from {device}")

        await client.connect_and_stream(duration=10, callback=on_audio)

    asyncio.run(main())
"""

__all__ = ['AudioStreamClient', 'AudioStreamError']

import asyncio
import base64
import json
import wave
from pathlib import Path
from typing import Callable, Optional
import logging

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


logger = logging.getLogger(__name__)


class AudioStreamError(Exception):
    """Exception raised for audio streaming errors."""
    pass


class AudioStreamClient:
    """Client for streaming audio from Vector via wirepod's websocket API.

    This client connects to a wirepod server that has been modified to
    broadcast Vector's microphone audio over websocket. Audio is streamed
    in real-time as 16-bit PCM at 16kHz.

    Args:
        host: The wirepod server IP address or hostname
        port: The wirepod web server port (default 8080)
        device: Optional Vector serial number to filter audio from a specific robot

    Example::

        client = AudioStreamClient(host="192.168.1.100")

        # Stream for 10 seconds and save to file
        audio = await client.connect_and_stream(
            duration=10,
            save_to_file="recording.wav"
        )
    """

    def __init__(self, host: str = "localhost", port: int = 8080, device: str = ""):
        if not WEBSOCKETS_AVAILABLE:
            raise AudioStreamError(
                "websockets library is required for audio streaming. "
                "Install with: pip install websockets"
            )

        self.host = host
        self.port = port
        self.device = device
        self._ws_url = f"ws://{host}:{port}/api-audio/stream"
        if device:
            self._ws_url += f"?device={device}"

        self._audio_buffer = bytearray()
        self._sample_rate = 16000
        self._channels = 1
        self._sample_width = 2  # 16-bit audio
        self._is_connected = False
        self._websocket = None

    @property
    def ws_url(self) -> str:
        """The websocket URL for the audio stream."""
        return self._ws_url

    @property
    def sample_rate(self) -> int:
        """Audio sample rate in Hz."""
        return self._sample_rate

    @property
    def channels(self) -> int:
        """Number of audio channels."""
        return self._channels

    @property
    def sample_width(self) -> int:
        """Sample width in bytes (2 for 16-bit)."""
        return self._sample_width

    @property
    def is_connected(self) -> bool:
        """Whether the client is currently connected to wirepod."""
        return self._is_connected

    def trigger_listen(self, serial: str = None) -> bool:
        """Trigger Vector to start listening without saying 'Hey Vector'.

        This sends a command to wirepod to make Vector start listening
        for voice input, which will cause audio to flow to the websocket.

        Args:
            serial: Vector's serial number. If not provided, uses the
                   device set in constructor or wirepod's default.

        Returns:
            True if successful, False otherwise

        Raises:
            AudioStreamError: If requests library is not available
        """
        if not REQUESTS_AVAILABLE:
            raise AudioStreamError(
                "requests library is required for trigger_listen. "
                "Install with: pip install requests"
            )

        url = f"http://{self.host}:{self.port}/api-audio/trigger_listen"
        device = serial or self.device
        if device:
            url += f"?serial={device}"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                logger.info("Triggered listen mode: %s", response.text)
                return True
            else:
                logger.warning(
                    "Failed to trigger listen: %d - %s",
                    response.status_code, response.text
                )
                return False
        except Exception as e:
            logger.error("Error triggering listen: %s", e)
            return False

    async def connect_and_stream(
        self,
        duration: float = None,
        save_to_file: str = None,
        callback: Callable[[bytes, str], None] = None
    ) -> bytes:
        """Connect to wirepod and stream audio.

        Args:
            duration: How long to stream in seconds. None for indefinite
                     (until connection closes or KeyboardInterrupt)
            save_to_file: Optional path to save audio as WAV file
            callback: Optional callback function called for each audio chunk.
                     Signature: callback(audio_bytes: bytes, device: str)

        Returns:
            The complete audio buffer as bytes

        Raises:
            AudioStreamError: If connection fails
        """
        logger.info("Connecting to %s...", self._ws_url)
        self._audio_buffer.clear()

        try:
            async with websockets.connect(self._ws_url) as ws:
                self._websocket = ws
                self._is_connected = True
                logger.info("Connected! Waiting for audio...")

                start_time = asyncio.get_event_loop().time()
                chunk_count = 0

                async for message in ws:
                    try:
                        data = json.loads(message)

                        if data.get("type") == "connected":
                            logger.info("Server info: %s", data)
                            self._sample_rate = data.get("sample_rate", 16000)
                            continue

                        # Extract audio data
                        device = data.get("device", "unknown")
                        audio_b64 = data.get("data")

                        if audio_b64:
                            # Decode base64 audio
                            audio_bytes = base64.b64decode(audio_b64)
                            self._audio_buffer.extend(audio_bytes)
                            chunk_count += 1

                            if chunk_count % 50 == 0:
                                elapsed = asyncio.get_event_loop().time() - start_time
                                logger.debug(
                                    "Received %d chunks, %d bytes (%.1fs) from %s",
                                    chunk_count, len(self._audio_buffer), elapsed, device
                                )

                            # Call callback if provided
                            if callback:
                                callback(audio_bytes, device)

                        # Check duration limit
                        if duration:
                            elapsed = asyncio.get_event_loop().time() - start_time
                            if elapsed >= duration:
                                logger.info("Duration limit reached (%.1fs)", duration)
                                break

                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON received: %s...", message[:100])

        except websockets.exceptions.ConnectionClosed as e:
            logger.info("Connection closed: %s", e)
        except Exception as e:
            logger.error("Error: %s", e)
            raise AudioStreamError(f"Stream error: {e}") from e
        finally:
            self._is_connected = False
            self._websocket = None

        # Save to file if requested
        if save_to_file and self._audio_buffer:
            self.save_wav(save_to_file)

        return bytes(self._audio_buffer)

    def save_wav(self, filepath: str) -> None:
        """Save buffered audio to WAV file.

        Args:
            filepath: Path to save the WAV file
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with wave.open(str(filepath), 'wb') as wav:
            wav.setnchannels(self._channels)
            wav.setsampwidth(self._sample_width)
            wav.setframerate(self._sample_rate)
            wav.writeframes(bytes(self._audio_buffer))

        duration = len(self._audio_buffer) / (
            self._sample_rate * self._sample_width * self._channels
        )
        logger.info("Saved %.2fs of audio to %s", duration, filepath)

    def get_audio_buffer(self) -> bytes:
        """Return the current audio buffer.

        Returns:
            The accumulated audio data as bytes
        """
        return bytes(self._audio_buffer)

    def clear_buffer(self) -> None:
        """Clear the audio buffer."""
        self._audio_buffer.clear()

    def get_buffer_duration(self) -> float:
        """Get the duration of audio in the buffer.

        Returns:
            Duration in seconds
        """
        return len(self._audio_buffer) / (
            self._sample_rate * self._sample_width * self._channels
        )


def check_wirepod_audio_support(host: str = "localhost", port: int = 8080) -> bool:
    """Check if wirepod server has audio streaming support.

    Args:
        host: wirepod server host
        port: wirepod server port

    Returns:
        True if audio streaming endpoint is available
    """
    if not REQUESTS_AVAILABLE:
        return False

    try:
        response = requests.get(
            f"http://{host}:{port}/api-audio/trigger_listen",
            timeout=5
        )
        # 400 (bad request) or 200 means endpoint exists
        return response.status_code in (200, 400)
    except Exception:
        return False
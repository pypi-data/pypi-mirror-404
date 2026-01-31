"""
ModelClient for the Reactor SDK.

This module handles the WebRTC connection to the model,
including video streaming and data channel messaging.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Optional, Set

import numpy as np
from aiortc import (
    MediaStreamTrack,
    RTCDataChannel,
    RTCIceServer,
    RTCPeerConnection,
    RTCRtpSender,
    RTCRtpTransceiver,
)
from aiortc.codecs import h264
from av import VideoFrame
from numpy.typing import NDArray

from reactor_sdk.types import FrameCallback, GPUMachineEvent, GPUMachineStatus
from reactor_sdk.utils.webrtc import (
    WebRTCConfig,
    create_data_channel,
    create_offer,
    create_peer_connection,
    parse_message,
    send_message,
    set_remote_description,
)

logger = logging.getLogger(__name__)


# Type for event handlers
GPUEventHandler = Callable[..., None]


class ModelClient:
    """
    Manages the WebRTC connection to the model.

    Handles video streaming (both receiving and sending), data channel
    messaging, and connection lifecycle.
    """

    def __init__(self, config: WebRTCConfig) -> None:
        """
        Initialize the GPUMachineClient.

        Args:
            config: WebRTC configuration including ICE servers.
        """
        self._config = config
        self._peer_connection: Optional[RTCPeerConnection] = None
        self._data_channel: Optional[RTCDataChannel] = None
        self._status: GPUMachineStatus = GPUMachineStatus.DISCONNECTED
        self._published_track: Optional[MediaStreamTrack] = None
        self._video_transceiver: Optional[RTCRtpTransceiver] = None
        self._remote_track: Optional[MediaStreamTrack] = None

        # Event system
        self._event_listeners: dict[GPUMachineEvent, Set[GPUEventHandler]] = {}

        # Frame callback for single-frame access
        self._frame_callback: Optional[FrameCallback] = None
        self._frame_task: Optional[asyncio.Task[None]] = None

        # Stop event for cooperative shutdown
        self._stop_event = asyncio.Event()

        # Connection state tracking - both must be true to be "connected"
        self._peer_connection_ready = False
        self._data_channel_open = False

    # =========================================================================
    # Event Emitter API
    # =========================================================================

    def on(self, event: GPUMachineEvent, handler: GPUEventHandler) -> None:
        """
        Register an event handler.

        Args:
            event: The event name.
            handler: The callback function.
        """
        if event not in self._event_listeners:
            self._event_listeners[event] = set()
        self._event_listeners[event].add(handler)

    def off(self, event: GPUMachineEvent, handler: GPUEventHandler) -> None:
        """
        Unregister an event handler.

        Args:
            event: The event name.
            handler: The callback function to remove.
        """
        if event in self._event_listeners:
            self._event_listeners[event].discard(handler)

    def _emit(self, event: GPUMachineEvent, *args: Any) -> None:
        """
        Emit an event to all registered handlers.

        Args:
            event: The event name.
            *args: Arguments to pass to handlers.
        """
        if event in self._event_listeners:
            for handler in self._event_listeners[event]:
                try:
                    handler(*args)
                except Exception as e:
                    logger.exception(f"Error in event handler for '{event}': {e}")

    # =========================================================================
    # Frame Callback
    # =========================================================================

    def set_frame_callback(self, callback: Optional[FrameCallback]) -> None:
        """
        Set a callback to receive individual video frames.

        The callback will be called with each received frame as a numpy array
        in RGB format with shape (H, W, 3).

        Args:
            callback: The callback function, or None to clear.
        """
        self._frame_callback = callback

    # =========================================================================
    # SDP & Connection
    # =========================================================================

    async def create_offer(self) -> str:
        """
        Create an SDP offer for initiating a connection.

        Must be called before connect().

        Returns:
            The SDP offer string.
        """
        # Create peer connection if not exists
        if self._peer_connection is None:
            self._peer_connection = create_peer_connection(self._config)
            self._setup_peer_connection_handlers()

        # Create data channel before offer (offerer creates the channel)
        self._data_channel = create_data_channel(
            self._peer_connection,
            self._config.data_channel_label,
        )
        self._setup_data_channel_handlers()

        # Add sendrecv video transceiver for bidirectional video
        self._video_transceiver = self._peer_connection.addTransceiver(
            "video",
            direction="sendrecv",
        )

        # Set codec preferences to prefer H.264 over VP8
        # This helps ensure codec compatibility with the server
        self._set_codec_preferences()

        offer = await create_offer(self._peer_connection)
        logger.debug("Created SDP offer")
        return offer

    def _set_codec_preferences(self) -> None:
        """
        Set codec preferences to prefer H.264 over VP8.

        H.264 is more widely supported and often provides better compatibility.
        """
        if self._video_transceiver is None:
            return

        try:
            # Get available video codecs
            capabilities = RTCRtpSender.getCapabilities("video")
            if capabilities is None:
                logger.debug("No video capabilities available")
                return

            # Sort codecs to prefer H.264, then VP8, then others
            preferred_codecs = []
            other_codecs = []

            for codec in capabilities.codecs:
                if codec.mimeType.lower() == "video/h264":
                    preferred_codecs.insert(0, codec)  # H.264 first
                elif codec.mimeType.lower() == "video/vp8":
                    preferred_codecs.append(codec)  # VP8 second
                else:
                    other_codecs.append(codec)

            # Combine: H.264 first, then VP8, then others
            all_codecs = preferred_codecs + other_codecs

            if all_codecs:
                self._video_transceiver.setCodecPreferences(all_codecs)
                codec_names = [c.mimeType for c in all_codecs[:3]]
                logger.debug(f"Set codec preferences: {codec_names}...")

        except Exception as e:
            # Don't fail if codec preferences can't be set
            logger.debug(f"Could not set codec preferences: {e}")

    async def connect(self, sdp_answer: str) -> None:
        """
        Connect to the GPU machine using the provided SDP answer.

        create_offer() must be called first.

        Args:
            sdp_answer: The SDP answer from the GPU machine.

        Raises:
            RuntimeError: If create_offer() was not called first.
        """
        if self._peer_connection is None:
            raise RuntimeError("Cannot connect - call create_offer() first")

        if self._peer_connection.signalingState != "have-local-offer":
            raise RuntimeError(
                f"Invalid signaling state: {self._peer_connection.signalingState}"
            )

        self._set_status(GPUMachineStatus.CONNECTING)

        try:
            await set_remote_description(self._peer_connection, sdp_answer)
            logger.debug("Remote description set")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self._set_status(GPUMachineStatus.ERROR)
            raise

    async def disconnect(self) -> None:
        """
        Disconnect from the GPU machine and clean up resources.
        """
        # Signal stop to frame processing task
        self._stop_event.set()

        # Cancel frame processing task
        if self._frame_task is not None:
            self._frame_task.cancel()
            try:
                await self._frame_task
            except asyncio.CancelledError:
                pass
            self._frame_task = None

        # Unpublish any published track
        if self._published_track is not None:
            await self.unpublish_track()

        # Close data channel
        if self._data_channel is not None:
            self._data_channel.close()
            self._data_channel = None

        # Close peer connection
        if self._peer_connection is not None:
            await self._peer_connection.close()
            self._peer_connection = None

        self._video_transceiver = None
        self._remote_track = None
        self._peer_connection_ready = False
        self._data_channel_open = False
        self._set_status(GPUMachineStatus.DISCONNECTED)
        logger.debug("Disconnected from GPU machine")

    def get_status(self) -> GPUMachineStatus:
        """
        Get the current connection status.

        Returns:
            The current GPUMachineStatus.
        """
        return self._status

    def get_local_sdp(self) -> Optional[str]:
        """
        Get the current local SDP description.

        Returns:
            The local SDP string, or None if not set.
        """
        if self._peer_connection is None:
            return None
        desc = self._peer_connection.localDescription
        return desc.sdp if desc else None

    def is_offer_still_valid(self) -> bool:
        """
        Check if the current offer is still valid.

        Returns:
            True if the offer is valid.
        """
        if self._peer_connection is None:
            return False
        return self._peer_connection.signalingState == "have-local-offer"

    # =========================================================================
    # Messaging
    # =========================================================================

    def send_command(self, command: str, data: Any) -> None:
        """
        Send a command to the GPU machine via the data channel.

        Args:
            command: The command type.
            data: The data to send with the command.

        Raises:
            RuntimeError: If the data channel is not available.
        """
        if self._data_channel is None:
            raise RuntimeError("Data channel not available")

        try:
            send_message(self._data_channel, command, data)
        except Exception as e:
            logger.warning(f"Failed to send message: {e}")
            raise

    # =========================================================================
    # Track Publishing
    # =========================================================================

    async def publish_track(self, track: MediaStreamTrack) -> None:
        """
        Publish a track to the GPU machine.

        Only one track can be published at a time.
        Uses the existing transceiver's sender to replace the track.

        Args:
            track: The MediaStreamTrack to publish.

        Raises:
            RuntimeError: If not connected or no video transceiver.
        """
        if self._peer_connection is None:
            raise RuntimeError("Cannot publish track - not initialized")

        if self._status != GPUMachineStatus.CONNECTED:
            raise RuntimeError("Cannot publish track - not connected")

        if self._video_transceiver is None:
            raise RuntimeError("Cannot publish track - no video transceiver")

        try:
            # Use replaceTrack on the existing transceiver's sender
            # This doesn't require renegotiation
            await self._video_transceiver.sender.replaceTrack(track)
            self._published_track = track
            logger.debug(f"Track published successfully: {track.kind}")
        except Exception as e:
            logger.error(f"Failed to publish track: {e}")
            raise

    async def unpublish_track(self) -> None:
        """
        Unpublish the currently published track.
        """
        if self._video_transceiver is None or self._published_track is None:
            return

        try:
            # Replace with None to stop sending without renegotiation
            await self._video_transceiver.sender.replaceTrack(None)
            logger.debug("Track unpublished successfully")
        except Exception as e:
            logger.error(f"Failed to unpublish track: {e}")
            raise
        finally:
            self._published_track = None

    def get_published_track(self) -> Optional[MediaStreamTrack]:
        """
        Get the currently published track.

        Returns:
            The published MediaStreamTrack, or None.
        """
        return self._published_track

    # =========================================================================
    # Remote Stream Access
    # =========================================================================

    def get_remote_track(self) -> Optional[MediaStreamTrack]:
        """
        Get the remote video track from the GPU machine.

        Returns:
            The remote MediaStreamTrack, or None if not available.
        """
        return self._remote_track

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _set_status(self, new_status: GPUMachineStatus) -> None:
        """Set the connection status and emit event if changed."""
        if self._status != new_status:
            self._status = new_status
            self._emit("status_changed", new_status)

    def _check_fully_connected(self) -> None:
        """
        Check if both peer connection and data channel are ready.

        Only transitions to CONNECTED status when both conditions are met.
        This prevents sending messages before the data channel is open.
        """
        if self._peer_connection_ready and self._data_channel_open:
            logger.debug("Both peer connection and data channel ready - fully connected")
            self._set_status(GPUMachineStatus.CONNECTED)

    def _setup_peer_connection_handlers(self) -> None:
        """Set up event handlers for the peer connection."""
        if self._peer_connection is None:
            return

        @self._peer_connection.on("connectionstatechange")
        async def on_connection_state_change() -> None:
            if self._peer_connection is None:
                return

            state = self._peer_connection.connectionState
            logger.debug(f"Peer connection state: {state}")

            if state == "connected":
                self._peer_connection_ready = True
                self._check_fully_connected()
            elif state in ("disconnected", "closed"):
                self._peer_connection_ready = False
                self._data_channel_open = False
                self._set_status(GPUMachineStatus.DISCONNECTED)
            elif state == "failed":
                self._peer_connection_ready = False
                self._set_status(GPUMachineStatus.ERROR)

        @self._peer_connection.on("track")
        def on_track(track: MediaStreamTrack) -> None:
            logger.debug(f"Track received: {track.kind}")
            if track.kind == "video":
                self._remote_track = track
                self._emit("track_received", track)
                # Start frame processing if callback is set
                if self._frame_callback is not None:
                    self._start_frame_processing(track)

        @self._peer_connection.on("icecandidate")
        def on_ice_candidate(candidate: Any) -> None:
            if candidate:
                logger.debug(f"ICE candidate: {candidate}")

        @self._peer_connection.on("datachannel")
        def on_data_channel(channel: RTCDataChannel) -> None:
            logger.debug(f"Data channel received from remote: {channel.label}")
            self._data_channel = channel
            self._setup_data_channel_handlers()

    def _setup_data_channel_handlers(self) -> None:
        """Set up event handlers for the data channel."""
        if self._data_channel is None:
            return

        @self._data_channel.on("open")
        def on_open() -> None:
            logger.debug("Data channel open")
            self._data_channel_open = True
            self._check_fully_connected()

        @self._data_channel.on("close")
        def on_close() -> None:
            logger.debug("Data channel closed")
            self._data_channel_open = False

        @self._data_channel.on("message")
        def on_message(message: str) -> None:
            data = parse_message(message)
            logger.debug(f"Received message: {data}")
            try:
                self._emit("application", data)
            except Exception as e:
                logger.error(f"Failed to handle message: {e}")

    def _start_frame_processing(self, track: MediaStreamTrack) -> None:
        """Start the frame processing task for the given track."""
        if self._frame_task is not None:
            self._frame_task.cancel()

        self._stop_event.clear()
        self._frame_task = asyncio.create_task(self._process_frames(track))

    async def _process_frames(self, track: MediaStreamTrack) -> None:
        """
        Process incoming video frames from a track.

        Args:
            track: The MediaStreamTrack to process frames from.
        """
        try:
            while not self._stop_event.is_set():
                try:
                    # Receive frame with timeout to allow stop checks
                    frame: VideoFrame = await asyncio.wait_for(
                        track.recv(),
                        timeout=0.1,
                    )

                    # Convert to numpy RGB array
                    numpy_frame = self._video_frame_to_numpy(frame)

                    # Call the frame callback
                    if self._frame_callback is not None:
                        try:
                            self._frame_callback(numpy_frame)
                        except Exception as e:
                            logger.error(f"Error in frame callback: {e}")

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    if "MediaStreamError" in str(type(e).__name__):
                        logger.debug("Video track ended")
                        break
                    logger.warning(f"Error processing video frame: {e}")
                    break

        except asyncio.CancelledError:
            logger.debug("Frame processing cancelled")
        except Exception as e:
            logger.warning(f"Frame processing stopped: {e}")
        finally:
            self._emit("track_removed")

    @staticmethod
    def _video_frame_to_numpy(frame: VideoFrame) -> NDArray[np.uint8]:
        """
        Convert an av.VideoFrame to a numpy array (H, W, 3) RGB.

        Args:
            frame: The VideoFrame to convert.

        Returns:
            Numpy array in RGB format with shape (H, W, 3).
        """
        if frame.format.name != "rgb24":
            frame = frame.reformat(format="rgb24")
        return frame.to_ndarray()


# =============================================================================
# Custom Video Track for Sending Frames
# =============================================================================


class FrameVideoTrack(MediaStreamTrack):
    """
    A video track that sends frames from a queue.

    Use this to send custom video frames to the GPU machine.

    Example:
        track = FrameVideoTrack()
        await reactor.publish_track(track)

        # Push frames in a loop
        while True:
            frame = get_next_frame()  # Your frame source
            await track.push_frame(frame)
    """

    kind = "video"

    def __init__(self, fps: float = 30.0) -> None:
        """
        Initialize the FrameVideoTrack.

        Args:
            fps: Target frames per second.
        """
        super().__init__()
        self._queue: asyncio.Queue[VideoFrame] = asyncio.Queue(maxsize=2)
        self._pts = 0
        self._fps = fps
        self._time_base = 1 / fps

    async def push_frame(self, frame: NDArray[np.uint8]) -> None:
        """
        Push a frame to be sent.

        Args:
            frame: Numpy array in RGB format with shape (H, W, 3).
        """
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame = video_frame.reformat(format="yuv420p")
        video_frame.pts = self._pts
        video_frame.time_base = self._time_base
        self._pts += 1

        # Non-blocking put, drop old frames if queue is full
        try:
            self._queue.put_nowait(video_frame)
        except asyncio.QueueFull:
            # Drop oldest frame and add new one
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            await self._queue.put(video_frame)

    async def recv(self) -> VideoFrame:
        """
        Receive the next frame to send.

        Returns:
            The next VideoFrame.
        """
        frame = await self._queue.get()
        return frame

    def stop(self) -> None:
        """Stop the track."""
        super().stop()

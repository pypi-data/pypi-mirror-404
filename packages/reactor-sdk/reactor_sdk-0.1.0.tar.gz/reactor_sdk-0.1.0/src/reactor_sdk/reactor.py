"""
Reactor - Main entry point for the Reactor Python SDK.

This module provides the main Reactor class that orchestrates the
coordinator and GPU machine clients for real-time AI video streaming.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Optional, Set, TypeVar, Union, overload

from aiortc import MediaStreamTrack

from reactor_sdk.coordinator import CoordinatorClient, LocalCoordinatorClient
from reactor_sdk.model import ModelClient
from reactor_sdk.types import (
    ConflictError,
    FrameCallback,
    GPUMachineStatus,
    ReactorError,
    ReactorEvent,
    ReactorState,
    ReactorStatus,
)
from reactor_sdk.utils.tokens import fetch_jwt_token
from reactor_sdk.utils.webrtc import WebRTCConfig

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

LOCAL_COORDINATOR_URL = "http://localhost:8080"
PROD_COORDINATOR_URL = "https://api.reactor.inc"


# Type for event handlers
EventHandler = Callable[..., None]

# Type variable for decorator return types
F = TypeVar("F", bound=Callable[..., Any])


# =============================================================================
# Reactor Implementation (Internal)
# =============================================================================


class _ReactorImpl:
    """
    Internal implementation of the Reactor class.

    Do not instantiate directly - use `Reactor(...)` instead.
    """

    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = None,
        coordinator_url: str = PROD_COORDINATOR_URL,
        local: bool = False,
    ) -> None:
        """
        Initialize the Reactor.

        Args:
            model_name: Name of the model to connect to.
            api_key: Your Reactor API key. The SDK will automatically fetch
                a JWT token using this key. Required unless local=True.
            coordinator_url: URL of the coordinator API (ignored if local=True).
            local: If True, use local coordinator at localhost:8080.
        """
        self._model = model_name
        self._api_key = api_key
        self._local = local
        self._coordinator_url = LOCAL_COORDINATOR_URL if local else coordinator_url

        # Clients
        self._coordinator_client: Optional[
            Union[CoordinatorClient, LocalCoordinatorClient]
        ] = None
        self._machine_client: Optional[ModelClient] = None

        # State
        self._status: ReactorStatus = ReactorStatus.DISCONNECTED
        self._session_id: Optional[str] = None
        self._session_expiration: Optional[float] = None
        self._last_error: Optional[ReactorError] = None

        # Event system
        self._event_listeners: dict[ReactorEvent, Set[EventHandler]] = {}

        # Frame callback (delegated to machine client)
        self._frame_callback: Optional[FrameCallback] = None

    # =========================================================================
    # Event Emitter API
    # =========================================================================

    def on(self, event: ReactorEvent, handler: EventHandler) -> None:
        """
        Register an event handler.

        Args:
            event: The event name.
            handler: The callback function.

        Events:
            - "status_changed": Called with (status: ReactorStatus)
            - "session_id_changed": Called with (session_id: str | None)
            - "new_message": Called with (message: dict)
            - "stream_changed": Called with (track: MediaStreamTrack)
            - "error": Called with (error: ReactorError)
            - "session_expiration_changed": Called with (expiration: float | None)
        """
        if event not in self._event_listeners:
            self._event_listeners[event] = set()
        self._event_listeners[event].add(handler)

    def off(self, event: ReactorEvent, handler: EventHandler) -> None:
        """
        Unregister an event handler.

        Args:
            event: The event name.
            handler: The callback function to remove.
        """
        if event in self._event_listeners:
            self._event_listeners[event].discard(handler)

    def _emit(self, event: ReactorEvent, *args: Any) -> None:
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
    # Decorator API
    # =========================================================================

    def on_frame(self, func: F) -> F:
        """
        Decorator to register a frame callback.

        The decorated function will be called with each received video frame
        as a numpy array in RGB format with shape (H, W, 3).

        Example:
            @reactor.on_frame
            def handle_frame(frame):
                print(f"Frame shape: {frame.shape}")

        Args:
            func: The callback function that receives a numpy frame.

        Returns:
            The original function (unchanged).
        """
        self.set_frame_callback(func)
        return func

    def on_message(self, func: F) -> F:
        """
        Decorator to register a message handler.

        The decorated function will be called with each message received
        from the GPU machine.

        Example:
            @reactor.on_message
            def handle_message(message):
                print(f"Received: {message}")

        Args:
            func: The callback function that receives the message dict.

        Returns:
            The original function (unchanged).
        """
        self.on("new_message", func)
        return func

    @overload
    def on_status(self, func: F) -> F:
        """Register handler for all status changes."""
        ...

    @overload
    def on_status(
        self, status_filter: ReactorStatus
    ) -> Callable[[F], F]:
        """Register handler for specific status."""
        ...

    @overload
    def on_status(
        self, status_filter: list[ReactorStatus]
    ) -> Callable[[F], F]:
        """Register handler for multiple specific statuses."""
        ...

    def on_status(
        self,
        func_or_filter: Union[F, ReactorStatus, list[ReactorStatus], None] = None,
    ) -> Union[F, Callable[[F], F]]:
        """
        Decorator to register a status change handler.

        Can be used with or without a filter argument:

        Example:
            # Handle all status changes
            @reactor.on_status
            def handle_any_status(status):
                print(f"Status: {status}")

            # Handle specific status only
            @reactor.on_status(ReactorStatus.READY)
            def handle_ready():
                print("Ready!")

            # Handle multiple statuses
            @reactor.on_status([ReactorStatus.READY, ReactorStatus.CONNECTING])
            def handle_active(status):
                print(f"Active state: {status}")

        Args:
            func_or_filter: Either the function to decorate (no filter),
                a single ReactorStatus, or a list of ReactorStatus values to filter on.

        Returns:
            The decorator or the decorated function.
        """
        # Case 1: @reactor.on_status (no parentheses, no filter)
        if callable(func_or_filter):
            func = func_or_filter
            self.on("status_changed", func)
            return func

        # Case 2: @reactor.on_status(ReactorStatus.READY) or
        #         @reactor.on_status([ReactorStatus.READY, ReactorStatus.CONNECTING])
        status_filter = func_or_filter

        # Normalize to a set for efficient lookup
        if status_filter is None:
            allowed_statuses: Optional[Set[ReactorStatus]] = None
        elif isinstance(status_filter, list):
            allowed_statuses = set(status_filter)
        else:
            allowed_statuses = {status_filter}

        def decorator(func: F) -> F:
            if allowed_statuses is None:
                # No filter - call for all status changes
                self.on("status_changed", func)
            else:
                # Filter - only call when status matches
                def filtered_handler(status: ReactorStatus) -> None:
                    if status in allowed_statuses:
                        func(status)

                self.on("status_changed", filtered_handler)
            return func

        return decorator

    def on_error(self, func: F) -> F:
        """
        Decorator to register an error handler.

        The decorated function will be called when an error occurs.

        Example:
            @reactor.on_error
            def handle_error(error):
                print(f"Error: {error.code} - {error.message}")

        Args:
            func: The callback function that receives the ReactorError.

        Returns:
            The original function (unchanged).
        """
        self.on("error", func)
        return func

    def on_stream(self, func: F) -> F:
        """
        Decorator to register a stream/track handler.

        The decorated function will be called when the video stream changes
        (i.e., when a new track is received from the GPU machine).

        Example:
            @reactor.on_stream
            def handle_stream(track):
                print(f"Stream changed: {track}")

        Args:
            func: The callback function that receives the MediaStreamTrack.

        Returns:
            The original function (unchanged).
        """
        self.on("stream_changed", func)
        return func

    # =========================================================================
    # Connection Management
    # =========================================================================

    async def connect(self) -> None:
        """
        Connect to the coordinator and GPU machine.

        If an API key was provided in the constructor, the SDK will
        automatically fetch a JWT token before connecting.

        Raises:
            ValueError: If no API key provided and not in local mode.
            RuntimeError: If connection fails.
        """
        logger.debug(f"Connecting, status: {self._status}")

        if self._api_key is None and not self._local:
            raise ValueError(
                "No API key provided and not in local mode. "
                "Pass api_key to the Reactor constructor."
            )

        if self._status != ReactorStatus.DISCONNECTED:
            raise RuntimeError("Already connected or connecting")

        self._set_status(ReactorStatus.CONNECTING)

        try:
            logger.debug("Connecting to coordinator")

            # Fetch JWT token if we have an API key
            jwt_token: Optional[str] = None
            if self._api_key is not None:
                logger.debug("Fetching JWT token from coordinator...")
                jwt_token = await fetch_jwt_token(
                    api_key=self._api_key,
                    coordinator_url=self._coordinator_url,
                )
                logger.debug("JWT token obtained successfully")

            # Create coordinator client
            if self._local:
                self._coordinator_client = LocalCoordinatorClient(self._coordinator_url)
            else:
                self._coordinator_client = CoordinatorClient(
                    base_url=self._coordinator_url,
                    jwt_token=jwt_token or "",
                    model=self._model,
                )

            # Get ICE servers from coordinator
            ice_servers = await self._coordinator_client.get_ice_servers()

            # Create GPU machine client and generate SDP offer
            config = WebRTCConfig(ice_servers=ice_servers)
            self._machine_client = ModelClient(config)
            self._setup_machine_client_handlers()

            # Set frame callback if one was registered
            if self._frame_callback is not None:
                self._machine_client.set_frame_callback(self._frame_callback)

            sdp_offer = await self._machine_client.create_offer()

            # Create session with coordinator
            session_id = await self._coordinator_client.create_session(sdp_offer)
            self._set_session_id(session_id)

            # Get SDP answer from coordinator
            sdp_answer = await self._coordinator_client.connect(session_id)

            # Connect to GPU machine with the answer
            await self._machine_client.connect(sdp_answer)

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._create_error(
                "CONNECTION_FAILED",
                f"Connection failed: {e}",
                "coordinator",
                recoverable=True,
            )
            self._set_status(ReactorStatus.DISCONNECTED)
            raise

    async def reconnect(self) -> None:
        """
        Reconnect to an existing session that may have been interrupted.

        Raises:
            RuntimeError: If no active session or reconnection fails.
        """
        if self._session_id is None or self._coordinator_client is None:
            logger.warning("No active session to reconnect to.")
            return

        if self._status == ReactorStatus.READY:
            logger.warning("Already connected, no need to reconnect.")
            return

        self._set_status(ReactorStatus.CONNECTING)

        if self._machine_client is None:
            # Get ICE servers from coordinator
            ice_servers = await self._coordinator_client.get_ice_servers()

            config = WebRTCConfig(ice_servers=ice_servers)
            self._machine_client = ModelClient(config)
            self._setup_machine_client_handlers()

        # Always calculate a new offer for reconnection
        sdp_offer = await self._machine_client.create_offer()

        try:
            # Send offer to coordinator and get answer
            sdp_answer = await self._coordinator_client.connect(
                self._session_id,
                sdp_offer,
            )

            # Connect to GPU machine with the answer
            await self._machine_client.connect(sdp_answer)
            self._set_status(ReactorStatus.READY)

        except ConflictError:
            logger.error("Reconnection failed: conflict error")
            await self.disconnect(recoverable=True)
            self._create_error(
                "RECONNECTION_FAILED",
                "Reconnection failed: connection conflict",
                "coordinator",
                recoverable=True,
            )
        except Exception as e:
            logger.error(f"Failed to reconnect: {e}")
            await self.disconnect(recoverable=False)
            self._create_error(
                "RECONNECTION_FAILED",
                f"Failed to reconnect: {e}",
                "coordinator",
                recoverable=True,
            )

    async def disconnect(self, recoverable: bool = False) -> None:
        """
        Disconnect from the coordinator and GPU machine.

        Args:
            recoverable: If True, keep session info for potential reconnection.
        """
        if self._status == ReactorStatus.DISCONNECTED and self._session_id is None:
            logger.warning("Already disconnected")
            return

        # Terminate coordinator session if not recoverable
        if self._coordinator_client is not None and not recoverable:
            try:
                await self._coordinator_client.terminate_session()
            except Exception as e:
                logger.error(f"Error terminating coordinator session: {e}")
            finally:
                await self._coordinator_client.close()
                self._coordinator_client = None

        # Disconnect machine client
        if self._machine_client is not None:
            try:
                await self._machine_client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting from GPU machine: {e}")

            if not recoverable:
                self._machine_client = None

        self._set_status(ReactorStatus.DISCONNECTED)

        if not recoverable:
            self._set_session_expiration(None)
            self._set_session_id(None)

    # =========================================================================
    # Communication
    # =========================================================================

    async def send_command(self, command: str, data: Any) -> None:
        """
        Send a command to the GPU machine.

        Args:
            command: The command type.
            data: The data to send with the command.
        """
        if self._status != ReactorStatus.READY:
            logger.warning(f"Cannot send message, status is {self._status}")
            return

        try:
            if self._machine_client is not None:
                self._machine_client.send_command(command, data)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self._create_error(
                "MESSAGE_SEND_FAILED",
                f"Failed to send message: {e}",
                "gpu",
                recoverable=True,
            )

    # =========================================================================
    # Track Publishing
    # =========================================================================

    async def publish_track(self, track: MediaStreamTrack) -> None:
        """
        Publish a video track to the GPU machine.

        Args:
            track: The MediaStreamTrack to publish.
        """
        if self._status != ReactorStatus.READY:
            logger.warning(f"Cannot publish track, status is {self._status}")
            return

        try:
            if self._machine_client is not None:
                await self._machine_client.publish_track(track)
        except Exception as e:
            logger.error(f"Failed to publish track: {e}")
            self._create_error(
                "TRACK_PUBLISH_FAILED",
                f"Failed to publish track: {e}",
                "gpu",
                recoverable=True,
            )

    async def unpublish_track(self) -> None:
        """
        Unpublish the currently published track.
        """
        try:
            if self._machine_client is not None:
                await self._machine_client.unpublish_track()
        except Exception as e:
            logger.error(f"Failed to unpublish track: {e}")
            self._create_error(
                "TRACK_UNPUBLISH_FAILED",
                f"Failed to unpublish track: {e}",
                "gpu",
                recoverable=True,
            )

    # =========================================================================
    # Frame Callback
    # =========================================================================

    def set_frame_callback(self, callback: Optional[FrameCallback]) -> None:
        """
        Set a callback to receive individual video frames.

        The callback will be called with each received frame as a numpy array
        in RGB format with shape (H, W, 3).

        This can be called before or after connect().

        Args:
            callback: The callback function, or None to clear.
        """
        self._frame_callback = callback

        # If already connected, update the machine client
        if self._machine_client is not None:
            self._machine_client.set_frame_callback(callback)

    # =========================================================================
    # Remote Stream Access
    # =========================================================================

    def get_remote_track(self) -> Optional[MediaStreamTrack]:
        """
        Get the remote video track from the GPU machine.

        Returns:
            The remote MediaStreamTrack, or None if not available.
        """
        if self._machine_client is None:
            return None
        return self._machine_client.get_remote_track()

    # =========================================================================
    # State Accessors
    # =========================================================================

    def get_status(self) -> ReactorStatus:
        """
        Get the current connection status.

        Returns:
            The current ReactorStatus.
        """
        return self._status

    def get_state(self) -> ReactorState:
        """
        Get the current state including status and error info.

        Returns:
            The current ReactorState.
        """
        return ReactorState(
            status=self._status,
            last_error=self._last_error,
        )

    def get_session_id(self) -> Optional[str]:
        """
        Get the current session ID.

        Returns:
            The session ID, or None if not connected.
        """
        return self._session_id

    def get_last_error(self) -> Optional[ReactorError]:
        """
        Get the last error that occurred.

        Returns:
            The last ReactorError, or None.
        """
        return self._last_error

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _set_status(self, new_status: ReactorStatus) -> None:
        """Set the status and emit event if changed."""
        logger.debug(f"Setting status: {new_status} from {self._status}")
        if self._status != new_status:
            self._status = new_status
            self._emit("status_changed", new_status)

    def _set_session_id(self, new_session_id: Optional[str]) -> None:
        """Set the session ID and emit event if changed."""
        logger.debug(f"Setting session ID: {new_session_id} from {self._session_id}")
        if self._session_id != new_session_id:
            self._session_id = new_session_id
            self._emit("session_id_changed", new_session_id)

    def _set_session_expiration(self, new_expiration: Optional[float]) -> None:
        """Set the session expiration and emit event if changed."""
        logger.debug(f"Setting session expiration: {new_expiration}")
        if self._session_expiration != new_expiration:
            self._session_expiration = new_expiration
            self._emit("session_expiration_changed", new_expiration)

    def _create_error(
        self,
        code: str,
        message: str,
        component: str,
        recoverable: bool,
        retry_after: Optional[float] = None,
    ) -> None:
        """Create and store an error, then emit the error event."""
        self._last_error = ReactorError(
            code=code,
            message=message,
            timestamp=time.time(),
            recoverable=recoverable,
            component=component,  # type: ignore
            retry_after=retry_after,
        )
        self._emit("error", self._last_error)

    def _setup_machine_client_handlers(self) -> None:
        """Set up event handlers for the machine client."""
        if self._machine_client is None:
            return

        def on_application(message: Any) -> None:
            self._emit("new_message", message)

        def on_status_changed(status: GPUMachineStatus) -> None:
            if status == GPUMachineStatus.CONNECTED:
                self._set_status(ReactorStatus.READY)
            elif status == GPUMachineStatus.DISCONNECTED:
                # Schedule disconnect on the event loop
                import asyncio
                asyncio.create_task(self.disconnect(recoverable=True))
            elif status == GPUMachineStatus.ERROR:
                self._create_error(
                    "GPU_CONNECTION_ERROR",
                    "GPU machine connection failed",
                    "gpu",
                    recoverable=True,
                )
                import asyncio
                asyncio.create_task(self.disconnect())

        def on_track_received(track: MediaStreamTrack) -> None:
            self._emit("stream_changed", track)

        self._machine_client.on("application", on_application)
        self._machine_client.on("status_changed", on_status_changed)
        self._machine_client.on("track_received", on_track_received)

    # =========================================================================
    # Context Manager
    # =========================================================================

    async def __aenter__(self) -> "_ReactorImpl":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        await self.disconnect()

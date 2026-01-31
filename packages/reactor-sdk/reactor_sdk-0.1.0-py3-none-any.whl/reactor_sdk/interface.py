"""
Reactor - Public API for the Reactor SDK.

This module defines the Reactor class that users interact with.
Internal implementation details are hidden in the reactor module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar, Union

from aiortc import MediaStreamTrack

from reactor_sdk.types import (
    FrameCallback,
    ReactorError,
    ReactorEvent,
    ReactorState,
    ReactorStatus,
)

# Type variable for decorator return types
F = TypeVar("F", bound=Callable[..., Any])

# Type for event handlers
EventHandler = Callable[..., None]

# Default coordinator URL
PROD_COORDINATOR_URL = "https://api.reactor.inc"


class Reactor:
    """
    Main entry point for the Reactor SDK.

    Provides real-time AI video streaming via WebRTC.

    Example:
        from reactor_sdk import Reactor, ReactorStatus

        reactor = Reactor(model_name="my-model", api_key="your-api-key")

        @reactor.on_frame
        def handle_frame(frame):
            print(f"Frame shape: {frame.shape}")

        @reactor.on_status(ReactorStatus.READY)
        def handle_ready(status):
            print("Connected!")

        await reactor.connect()
        await reactor.send_command("setParameter", {"value": 0.5})
        await reactor.disconnect()
    """

    def __new__(
        cls,
        model_name: str,
        api_key: Optional[str] = None,
        coordinator_url: str = PROD_COORDINATOR_URL,
        local: bool = False,
    ) -> "Reactor":
        """
        Create a new Reactor instance.

        Args:
            model_name: Name of the model to connect to.
            api_key: Your Reactor API key. The SDK will automatically fetch
                a JWT token using this key. Required unless local=True.
            coordinator_url: URL of the coordinator API (ignored if local=True).
            local: If True, use local coordinator at localhost:8080.

        Returns:
            A Reactor instance ready to be connected.
        """
        # Import here to avoid circular imports
        from reactor_sdk.reactor import _ReactorImpl

        return _ReactorImpl(  # type: ignore[return-value]
            model_name=model_name,
            api_key=api_key,
            coordinator_url=coordinator_url,
            local=local,
        )

    # =========================================================================
    # Event Registration
    # =========================================================================

    def on(self, event: ReactorEvent, handler: EventHandler) -> None:
        """Register an event handler."""
        ...

    def off(self, event: ReactorEvent, handler: EventHandler) -> None:
        """Unregister an event handler."""
        ...

    # =========================================================================
    # Decorators
    # =========================================================================

    def on_frame(self, func: F) -> F:
        """Decorator to register a frame callback."""
        ...

    def on_message(self, func: F) -> F:
        """Decorator to register a message handler."""
        ...

    def on_status(
        self,
        func_or_filter: Union[F, ReactorStatus, list[ReactorStatus], None] = None,
    ) -> Union[F, Callable[[F], F]]:
        """Decorator to register a status change handler (with optional filter)."""
        ...

    def on_error(self, func: F) -> F:
        """Decorator to register an error handler."""
        ...

    def on_stream(self, func: F) -> F:
        """Decorator to register a stream/track handler."""
        ...

    # =========================================================================
    # Connection
    # =========================================================================

    async def connect(self) -> None:
        """Connect to the coordinator and model."""
        ...

    async def reconnect(self) -> None:
        """Reconnect to an existing session."""
        ...

    async def disconnect(self, recoverable: bool = False) -> None:
        """Disconnect from the coordinator and model."""
        ...

    # =========================================================================
    # Communication
    # =========================================================================

    async def send_command(self, command: str, data: Any) -> None:
        """Send a command to the model."""
        ...

    # =========================================================================
    # Track Publishing
    # =========================================================================

    async def publish_track(self, track: MediaStreamTrack) -> None:
        """Publish a video track to the model."""
        ...

    async def unpublish_track(self) -> None:
        """Unpublish the currently published track."""
        ...

    # =========================================================================
    # Frame Callback
    # =========================================================================

    def set_frame_callback(self, callback: Optional[FrameCallback]) -> None:
        """Set a callback to receive individual video frames."""
        ...

    # =========================================================================
    # State Accessors
    # =========================================================================

    def get_remote_track(self) -> Optional[MediaStreamTrack]:
        """Get the remote video track from the model."""
        ...

    def get_status(self) -> ReactorStatus:
        """Get the current connection status."""
        ...

    def get_state(self) -> ReactorState:
        """Get the current state including status and error info."""
        ...

    def get_session_id(self) -> Optional[str]:
        """Get the current session ID."""
        ...

    def get_last_error(self) -> Optional[ReactorError]:
        """Get the last error that occurred."""
        ...

    # =========================================================================
    # Context Manager
    # =========================================================================

    async def __aenter__(self) -> "Reactor":
        """Async context manager entry."""
        ...

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        ...

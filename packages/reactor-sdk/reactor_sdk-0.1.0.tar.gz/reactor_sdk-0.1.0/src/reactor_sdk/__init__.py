"""
Reactor Python SDK - Real-time AI video streaming.

This SDK provides a Python interface for connecting to Reactor models
and streaming video in real-time using WebRTC.

Example:
    from reactor_sdk import Reactor, ReactorStatus

    reactor = Reactor(model_name="my-model", api_key="your-api-key")

    @reactor.on_frame
    def handle_frame(frame):
        print(f"Frame: {frame.shape}")

    @reactor.on_status(ReactorStatus.READY)
    def handle_ready(status):
        print("Connected!")

    await reactor.connect()
"""

# Main class
from reactor_sdk.interface import Reactor

# Types
from reactor_sdk.types import (
    ConflictError,
    FrameCallback,
    GPUMachineEvent,
    GPUMachineStatus,
    ReactorError,
    ReactorEvent,
    ReactorState,
    ReactorStatus,
)

# Utilities
from reactor_sdk.utils.tokens import fetch_jwt_token

__all__ = [
    # Main class
    "Reactor",
    # Utilities
    "fetch_jwt_token",
    # Types
    "ReactorStatus",
    "ReactorError",
    "ReactorState",
    "ReactorEvent",
    "GPUMachineStatus",
    "GPUMachineEvent",
    "FrameCallback",
    "ConflictError",
]

__version__ = "0.1.0"

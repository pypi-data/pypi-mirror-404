"""
Type definitions for the Reactor SDK.

This module contains all the type definitions, enums, and data classes
used throughout the SDK.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Literal, Optional, TypedDict

import numpy as np
from numpy.typing import NDArray


# =============================================================================
# Status Enums
# =============================================================================


class ReactorStatus(Enum):
    """Status of the Reactor connection."""

    DISCONNECTED = "disconnected"  # Not connected to anything
    CONNECTING = "connecting"  # Establishing connection to coordinator
    WAITING = "waiting"  # Connected to coordinator, waiting for GPU assignment
    READY = "ready"  # Connected to GPU machine, can send/receive messages


class GPUMachineStatus(Enum):
    """Status of the GPU machine WebRTC connection."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


# =============================================================================
# Event Types
# =============================================================================

# Reactor event types
ReactorEvent = Literal[
    "status_changed",  # Updates on the reactor status
    "session_id_changed",  # Updates on the session ID
    "new_message",  # New messages from the machine
    "stream_changed",  # Video stream has changed
    "error",  # Error events with ReactorError details
    "session_expiration_changed",  # Session expiration has changed
]

# GPU Machine event types
GPUMachineEvent = Literal[
    "status_changed",  # Connection state changes
    "track_received",  # Remote track received
    "track_removed",  # Remote track removed
    "application",  # Data channel messages
]


# =============================================================================
# Error Types
# =============================================================================


@dataclass
class ReactorError:
    """Information about an error that occurred in the Reactor."""

    code: str
    message: str
    timestamp: float
    recoverable: bool
    component: Literal["coordinator", "gpu"]
    retry_after: Optional[float] = None

    def __str__(self) -> str:
        return f"[{self.component}:{self.code}] {self.message}"


class ConflictError(Exception):
    """Raised when a connection conflict occurs (e.g., superseded by newer request)."""

    pass


# =============================================================================
# State Types
# =============================================================================


@dataclass
class ReactorState:
    """Current state of the Reactor including status and error info."""

    status: ReactorStatus
    last_error: Optional[ReactorError] = None


# =============================================================================
# Callback Types
# =============================================================================

# Type for frame callback function - receives numpy RGB frame (H, W, 3)
FrameCallback = Callable[[NDArray[np.uint8]], None]

# Type for event handler function
EventHandler = Callable[..., None]


# =============================================================================
# API Response Types
# =============================================================================


class IceServerCredentials(TypedDict, total=False):
    """Credentials for an ICE server."""

    username: str
    password: str


class IceServerConfig(TypedDict):
    """Configuration for a single ICE server."""

    uris: list[str]
    credentials: Optional[IceServerCredentials]


class IceServersResponse(TypedDict):
    """Response from the ICE servers endpoint."""

    ice_servers: list[IceServerConfig]


class ModelConfig(TypedDict):
    """Model configuration in session requests."""

    name: str


class CreateSessionRequest(TypedDict):
    """Request body for creating a session."""

    model: ModelConfig
    sdp_offer: str
    extra_args: dict[str, Any]


class CreateSessionResponse(TypedDict):
    """Response from creating a session."""

    session_id: str


class SDPParamsRequest(TypedDict):
    """Request body for SDP params endpoint."""

    sdp_offer: str
    extra_args: dict[str, Any]


class SDPParamsResponse(TypedDict):
    """Response from SDP params endpoint."""

    sdp_answer: str
    extra_args: dict[str, Any]


class SessionState(Enum):
    """State of a session on the coordinator."""

    CREATED = "CREATED"
    PENDING = "PENDING"
    SUSPENDED = "SUSPENDED"
    WAITING = "WAITING"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CLOSED = "CLOSED"


class SessionInfoResponse(TypedDict):
    """Response from session info endpoint."""

    session_id: str
    state: str


# =============================================================================
# WebRTC Types
# =============================================================================


@dataclass
class RTCIceServer:
    """ICE server configuration for WebRTC."""

    urls: list[str]
    username: Optional[str] = None
    credential: Optional[str] = None


@dataclass
class WebRTCConfig:
    """Configuration for WebRTC peer connection."""

    ice_servers: list[RTCIceServer]
    data_channel_label: str = "data"


# =============================================================================
# Command Schema Types (for capabilities)
# =============================================================================


class ParameterSchema(TypedDict, total=False):
    """Schema for a command parameter."""

    description: str
    type: str  # "number", "integer", "string", "boolean"
    minimum: float
    maximum: float
    required: bool
    enum: list[str]


class CommandSchema(TypedDict):
    """Schema for a command."""

    description: str
    schema: dict[str, ParameterSchema]


class CapabilitiesMessage(TypedDict):
    """Message containing model capabilities/commands."""

    commands: dict[str, CommandSchema]


# =============================================================================
# Video Frame Types
# =============================================================================


@dataclass
class VideoFrameInfo:
    """Information about a video frame."""

    width: int
    height: int
    format: str = "rgb24"
    timestamp: float = field(default=0.0)

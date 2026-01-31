"""
WebRTC utility functions for the Reactor SDK.

This module provides stateless utility functions for WebRTC operations
using aiortc.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

from aiortc import RTCConfiguration, RTCDataChannel, RTCIceServer, RTCPeerConnection
from aiortc import RTCSessionDescription

from reactor_sdk.types import IceServersResponse

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class WebRTCConfig:
    """Configuration for WebRTC peer connection."""

    ice_servers: list[RTCIceServer]
    data_channel_label: str = "data"


DEFAULT_DATA_CHANNEL_LABEL = "data"
DEFAULT_ICE_GATHERING_TIMEOUT = 5.0  # seconds


# =============================================================================
# Peer Connection Creation
# =============================================================================


def create_peer_connection(config: WebRTCConfig) -> RTCPeerConnection:
    """
    Create a new RTCPeerConnection with the specified configuration.

    Args:
        config: WebRTC configuration with ICE servers.

    Returns:
        A new RTCPeerConnection instance.
    """
    rtc_config = RTCConfiguration(iceServers=config.ice_servers)
    return RTCPeerConnection(configuration=rtc_config)


def create_data_channel(
    pc: RTCPeerConnection,
    label: Optional[str] = None,
) -> RTCDataChannel:
    """
    Create a data channel on the peer connection.

    Args:
        pc: The RTCPeerConnection.
        label: Label for the data channel (defaults to "data").

    Returns:
        The created RTCDataChannel.
    """
    return pc.createDataChannel(label or DEFAULT_DATA_CHANNEL_LABEL)


# =============================================================================
# SDP Offer/Answer
# =============================================================================


async def create_offer(pc: RTCPeerConnection) -> str:
    """
    Create an SDP offer on the peer connection.

    Waits for ICE gathering to complete before returning.

    Args:
        pc: The RTCPeerConnection.

    Returns:
        The SDP offer string.

    Raises:
        RuntimeError: If local description creation fails.
    """
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    await wait_for_ice_gathering(pc)

    local_description = pc.localDescription
    if local_description is None:
        raise RuntimeError("Failed to create local description")

    return local_description.sdp


async def create_answer(pc: RTCPeerConnection, offer_sdp: str) -> str:
    """
    Create an SDP answer in response to a received offer.

    Waits for ICE gathering to complete before returning.

    Args:
        pc: The RTCPeerConnection.
        offer_sdp: The SDP offer string from the remote peer.

    Returns:
        The SDP answer string.

    Raises:
        RuntimeError: If local description creation fails.
    """
    await set_remote_description(pc, offer_sdp, "offer")

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    await wait_for_ice_gathering(pc)

    local_description = pc.localDescription
    if local_description is None:
        raise RuntimeError("Failed to create local description")

    return local_description.sdp


async def set_remote_description(
    pc: RTCPeerConnection,
    sdp: str,
    sdp_type: str = "answer",
) -> None:
    """
    Set the remote description on the peer connection.

    Args:
        pc: The RTCPeerConnection.
        sdp: The SDP string.
        sdp_type: The type of SDP ("offer" or "answer").
    """
    session_description = RTCSessionDescription(sdp=sdp, type=sdp_type)
    await pc.setRemoteDescription(session_description)


def get_local_description(pc: RTCPeerConnection) -> Optional[str]:
    """
    Get the local SDP description from the peer connection.

    Args:
        pc: The RTCPeerConnection.

    Returns:
        The local SDP string, or None if not set.
    """
    desc = pc.localDescription
    if desc is None:
        return None
    return desc.sdp


# =============================================================================
# ICE Handling
# =============================================================================


def transform_ice_servers(response: IceServersResponse) -> list[RTCIceServer]:
    """
    Transform ICE servers from the coordinator API format to RTCIceServer format.

    Args:
        response: The parsed IceServersResponse from the coordinator.

    Returns:
        List of RTCIceServer objects for WebRTC peer connection configuration.
    """
    ice_servers: list[RTCIceServer] = []

    for server in response["ice_servers"]:
        if server.get("credentials"):
            creds = server["credentials"]
            ice_server = RTCIceServer(
                urls=server["uris"],
                username=creds.get("username"),
                credential=creds.get("password"),
            )
        else:
            ice_server = RTCIceServer(urls=server["uris"])

        ice_servers.append(ice_server)

    return ice_servers


async def wait_for_ice_gathering(
    pc: RTCPeerConnection,
    timeout: float = DEFAULT_ICE_GATHERING_TIMEOUT,
) -> None:
    """
    Wait for ICE gathering to complete with a timeout.

    Args:
        pc: The RTCPeerConnection.
        timeout: Maximum time to wait in seconds.
    """
    if pc.iceGatheringState == "complete":
        return

    gathering_complete = asyncio.Event()

    @pc.on("icegatheringstatechange")
    def on_ice_gathering_state_change() -> None:
        if pc.iceGatheringState == "complete":
            gathering_complete.set()

    try:
        await asyncio.wait_for(gathering_complete.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(
            f"ICE gathering timed out after {timeout}s, proceeding with current candidates"
        )


# =============================================================================
# Data Channel Messaging
# =============================================================================


def send_message(channel: RTCDataChannel, command: str, data: Any) -> None:
    """
    Send a message through a data channel.

    Args:
        channel: The RTCDataChannel.
        command: The command type.
        data: The data to send with the command.

    Raises:
        RuntimeError: If the data channel is not open.
    """
    if channel.readyState != "open":
        raise RuntimeError(f"Data channel not open: {channel.readyState}")

    json_data = data if isinstance(data, dict) else json.loads(data) if isinstance(data, str) else data
    payload = {"type": command, "data": json_data}
    channel.send(json.dumps(payload))


def parse_message(data: Any) -> Any:
    """
    Parse a received data channel message, attempting JSON parse.

    Args:
        data: The raw message data.

    Returns:
        The parsed message (dict if JSON, otherwise original data).
    """
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data
    return data


# =============================================================================
# Connection State
# =============================================================================


def is_connected(pc: RTCPeerConnection) -> bool:
    """
    Check if the peer connection is in a connected state.

    Args:
        pc: The RTCPeerConnection.

    Returns:
        True if connected.
    """
    return pc.connectionState == "connected"


def is_closed(pc: RTCPeerConnection) -> bool:
    """
    Check if the peer connection is closed or failed.

    Args:
        pc: The RTCPeerConnection.

    Returns:
        True if closed or failed.
    """
    return pc.connectionState in ("closed", "failed")


async def close_peer_connection(pc: RTCPeerConnection) -> None:
    """
    Close the peer connection and clean up.

    Args:
        pc: The RTCPeerConnection.
    """
    await pc.close()

"""
LocalCoordinatorClient for the Reactor SDK.

This module provides a coordinator client for local development,
extending CoordinatorClient with simplified local endpoints.
"""

from __future__ import annotations

import logging
from typing import Optional

from aiortc import RTCIceServer

from reactor_sdk.coordinator.client import CoordinatorClient
from reactor_sdk.types import ConflictError, IceServersResponse
from reactor_sdk.utils.webrtc import transform_ice_servers

logger = logging.getLogger(__name__)


class LocalCoordinatorClient(CoordinatorClient):
    """
    Coordinator client for local development.

    Extends CoordinatorClient and overrides methods for local development
    endpoints that don't require authentication.
    """

    def __init__(self, base_url: str) -> None:
        """
        Initialize the LocalCoordinatorClient.

        Args:
            base_url: Base URL of the local coordinator (e.g., http://localhost:8080).
        """
        # Pass dummy values to parent - they won't be used for local
        super().__init__(
            base_url=base_url,
            jwt_token="local",
            model="local",
        )
        self._local_base_url = base_url.rstrip("/")
        self._sdp_offer: Optional[str] = None

    def _get_auth_headers(self) -> dict[str, str]:
        """
        Get headers for local requests (no auth required).

        Returns:
            Headers dict with Content-Type only.
        """
        return {"Content-Type": "application/json"}

    async def get_ice_servers(self) -> list[RTCIceServer]:
        """
        Get ICE servers from the local HTTP runtime.

        Returns:
            List of RTCIceServer objects.

        Raises:
            RuntimeError: If the request fails.
        """
        logger.debug("Fetching ICE servers from local coordinator...")

        session = await self._get_session()
        url = f"{self._local_base_url}/ice_servers"

        async with session.get(url) as response:
            if not response.ok:
                raise RuntimeError("Failed to get ICE servers from local coordinator.")

            data: IceServersResponse = await response.json()
            ice_servers = transform_ice_servers(data)

            logger.debug(f"Received {len(ice_servers)} ICE servers from local coordinator")
            return ice_servers

    async def create_session(self, sdp_offer: str) -> str:
        """
        Create a local session by posting to /start_session.

        Args:
            sdp_offer: The SDP offer string (stored for later use).

        Returns:
            Always returns "local" as the session ID.

        Raises:
            RuntimeError: If the request fails.
        """
        logger.debug("Creating local session...")

        self._sdp_offer = sdp_offer

        session = await self._get_session()
        url = f"{self._local_base_url}/start_session"

        async with session.post(url) as response:
            if not response.ok:
                raise RuntimeError("Failed to send local start session command.")

            logger.debug("Local session created")
            return "local"

    async def connect(
        self,
        session_id: str,
        sdp_offer: Optional[str] = None,
    ) -> str:
        """
        Connect to the local session by posting SDP params to /sdp_params.

        Args:
            session_id: The session ID (ignored for local).
            sdp_offer: The SDP offer from the local WebRTC peer connection.

        Returns:
            The SDP answer from the server.

        Raises:
            ConflictError: If the connection is superseded by a newer request.
            RuntimeError: If the request fails.
        """
        # Use provided offer or the stored one from create_session
        self._sdp_offer = sdp_offer or self._sdp_offer

        logger.debug("Connecting to local session...")

        session = await self._get_session()
        url = f"{self._local_base_url}/sdp_params"

        sdp_body = {
            "sdp": self._sdp_offer,
            "type": "offer",
        }

        async with session.post(
            url,
            headers=self._get_auth_headers(),
            json=sdp_body,
        ) as response:
            if not response.ok:
                if response.status == 409:
                    raise ConflictError("Connection superseded by newer request")
                raise RuntimeError("Failed to get SDP answer from local coordinator.")

            data = await response.json()
            logger.debug("Received SDP answer from local coordinator")
            return data["sdp"]

    async def terminate_session(self) -> None:
        """
        Stop the local session by posting to /stop_session.
        """
        logger.debug("Stopping local session...")

        session = await self._get_session()
        url = f"{self._local_base_url}/stop_session"

        await session.post(url)
        self._current_session_id = None

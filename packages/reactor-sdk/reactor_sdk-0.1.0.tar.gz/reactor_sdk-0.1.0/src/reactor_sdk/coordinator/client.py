"""
CoordinatorClient for the Reactor SDK.

This module handles HTTP communication with the Reactor coordinator
for session management and WebRTC signaling.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import aiohttp
from aiortc import RTCIceServer

from reactor_sdk.types import (
    CreateSessionRequest,
    CreateSessionResponse,
    IceServersResponse,
    SDPParamsRequest,
    SDPParamsResponse,
    SessionInfoResponse,
)
from reactor_sdk.utils.webrtc import transform_ice_servers

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

# Polling configuration for async SDP answer retrieval
INITIAL_BACKOFF_MS = 500
MAX_BACKOFF_MS = 30000
BACKOFF_MULTIPLIER = 2


# =============================================================================
# CoordinatorClient
# =============================================================================


class CoordinatorClient:
    """
    HTTP client for communicating with the Reactor coordinator.

    Handles session creation, SDP exchange, and ICE server retrieval.
    """

    def __init__(
        self,
        base_url: str,
        jwt_token: str,
        model: str,
    ) -> None:
        """
        Initialize the CoordinatorClient.

        Args:
            base_url: Base URL of the coordinator API.
            jwt_token: JWT token for authentication.
            model: Name of the model to connect to.
        """
        self._base_url = base_url.rstrip("/")
        self._jwt_token = jwt_token
        self._model = model
        self._current_session_id: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None

    def _get_auth_headers(self) -> dict[str, str]:
        """Get authorization headers with JWT Bearer token."""
        return {
            "Authorization": f"Bearer {self._jwt_token}",
            "Content-Type": "application/json",
        }

    # =========================================================================
    # ICE Servers
    # =========================================================================

    async def get_ice_servers(self) -> list[RTCIceServer]:
        """
        Fetch ICE servers from the coordinator.

        Returns:
            List of RTCIceServer objects for WebRTC peer connection configuration.

        Raises:
            aiohttp.ClientError: If the request fails.
        """
        logger.debug("Fetching ICE servers...")

        session = await self._get_session()
        url = f"{self._base_url}/ice_servers?model={self._model}"

        async with session.get(url, headers=self._get_auth_headers()) as response:
            if not response.ok:
                text = await response.text()
                raise RuntimeError(f"Failed to fetch ICE servers: {response.status} {text}")

            data: IceServersResponse = await response.json()
            ice_servers = transform_ice_servers(data)

            logger.debug(f"Received {len(ice_servers)} ICE servers")
            return ice_servers

    # =========================================================================
    # Session Management
    # =========================================================================

    async def create_session(self, sdp_offer: str) -> str:
        """
        Create a new session with the coordinator.

        Args:
            sdp_offer: The SDP offer from the local WebRTC peer connection.

        Returns:
            The session ID.

        Raises:
            aiohttp.ClientError: If the request fails.
        """
        logger.debug("Creating session...")

        session = await self._get_session()
        url = f"{self._base_url}/sessions"

        request_body: CreateSessionRequest = {
            "model": {"name": self._model},
            "sdp_offer": sdp_offer,
            "extra_args": {},
        }

        async with session.post(
            url,
            headers=self._get_auth_headers(),
            json=request_body,
        ) as response:
            if not response.ok:
                text = await response.text()
                raise RuntimeError(f"Failed to create session: {response.status} {text}")

            data: CreateSessionResponse = await response.json()
            self._current_session_id = data["session_id"]

            logger.debug(f"Session created with ID: {self._current_session_id}")
            return data["session_id"]

    async def get_session_info(self) -> SessionInfoResponse:
        """
        Get the current session information from the coordinator.

        Returns:
            The session info response.

        Raises:
            RuntimeError: If no active session exists.
            aiohttp.ClientError: If the request fails.
        """
        if self._current_session_id is None:
            raise RuntimeError("No active session. Call create_session() first.")

        logger.debug(f"Getting session info for: {self._current_session_id}")

        session = await self._get_session()
        url = f"{self._base_url}/sessions/{self._current_session_id}"

        async with session.get(url, headers=self._get_auth_headers()) as response:
            if not response.ok:
                text = await response.text()
                raise RuntimeError(f"Failed to get session: {response.status} {text}")

            data: SessionInfoResponse = await response.json()
            return data

    async def terminate_session(self) -> None:
        """
        Terminate the current session.

        Raises:
            RuntimeError: If no active session exists or termination fails.
        """
        if self._current_session_id is None:
            raise RuntimeError("No active session. Call create_session() first.")

        logger.debug(f"Terminating session: {self._current_session_id}")

        session = await self._get_session()
        url = f"{self._base_url}/sessions/{self._current_session_id}"

        async with session.delete(url, headers=self._get_auth_headers()) as response:
            if response.ok:
                self._current_session_id = None
                return

            if response.status == 404:
                # Session doesn't exist on server, clear local state
                logger.debug(
                    f"Session not found on server, clearing local state: "
                    f"{self._current_session_id}"
                )
                self._current_session_id = None
                return

            # For other error codes, throw without clearing state
            text = await response.text()
            raise RuntimeError(f"Failed to terminate session: {response.status} {text}")

    def get_session_id(self) -> Optional[str]:
        """Get the current session ID."""
        return self._current_session_id

    # =========================================================================
    # SDP Exchange
    # =========================================================================

    async def _send_sdp_offer(
        self,
        session_id: str,
        sdp_offer: str,
    ) -> Optional[str]:
        """
        Send an SDP offer to the server for reconnection.

        Args:
            session_id: The session ID to connect to.
            sdp_offer: The SDP offer from the local WebRTC peer connection.

        Returns:
            The SDP answer if ready (200), or None if pending (202).

        Raises:
            aiohttp.ClientError: If the request fails.
        """
        logger.debug(f"Sending SDP offer for session: {session_id}")

        session = await self._get_session()
        url = f"{self._base_url}/sessions/{session_id}/sdp_params"

        request_body: SDPParamsRequest = {
            "sdp_offer": sdp_offer,
            "extra_args": {},
        }

        async with session.put(
            url,
            headers=self._get_auth_headers(),
            json=request_body,
        ) as response:
            if response.status == 200:
                data: SDPParamsResponse = await response.json()
                logger.debug("Received SDP answer immediately")
                return data["sdp_answer"]

            if response.status == 202:
                logger.debug("SDP offer accepted, answer pending (202)")
                return None

            text = await response.text()
            raise RuntimeError(f"Failed to send SDP offer: {response.status} {text}")

    async def _poll_sdp_answer(self, session_id: str) -> str:
        """
        Poll for the SDP answer with geometric backoff.

        Used for async reconnection when the answer is not immediately available.

        Args:
            session_id: The session ID to poll for.

        Returns:
            The SDP answer from the server.

        Raises:
            RuntimeError: If polling fails.
        """
        logger.debug(f"Polling for SDP answer for session: {session_id}")

        backoff_ms = INITIAL_BACKOFF_MS
        attempt = 0

        session = await self._get_session()
        url = f"{self._base_url}/sessions/{session_id}/sdp_params"

        while True:
            attempt += 1
            logger.debug(f"SDP poll attempt {attempt} for session {session_id}")

            async with session.get(url, headers=self._get_auth_headers()) as response:
                if response.status == 200:
                    data: SDPParamsResponse = await response.json()
                    logger.debug("Received SDP answer via polling")
                    return data["sdp_answer"]

                if response.status == 202:
                    logger.warning(
                        f"SDP answer pending (202), retrying in {backoff_ms}ms..."
                    )
                    await asyncio.sleep(backoff_ms / 1000)
                    backoff_ms = min(backoff_ms * BACKOFF_MULTIPLIER, MAX_BACKOFF_MS)
                    continue

                # For other error codes, throw immediately
                text = await response.text()
                raise RuntimeError(f"Failed to poll SDP answer: {response.status} {text}")

    async def connect(
        self,
        session_id: str,
        sdp_offer: Optional[str] = None,
    ) -> str:
        """
        Connect to the session by sending an SDP offer and receiving an SDP answer.

        If sdp_offer is provided, sends it first. If the answer is pending (202),
        falls back to polling. If no sdp_offer is provided, goes directly to polling.

        Args:
            session_id: The session ID to connect to.
            sdp_offer: Optional SDP offer from the local WebRTC peer connection.

        Returns:
            The SDP answer from the server.
        """
        logger.debug(f"Connecting to session: {session_id}")

        if sdp_offer:
            # Reconnection: we have a new SDP offer
            answer = await self._send_sdp_offer(session_id, sdp_offer)
            if answer is not None:
                return answer
            # Server accepted but answer not ready yet (202), fall back to polling

        # No SDP offer = async reconnection, poll until server has the answer
        return await self._poll_sdp_answer(session_id)

    # =========================================================================
    # Cleanup
    # =========================================================================

    async def __aenter__(self) -> "CoordinatorClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        await self.close()

"""
Token utilities for the Reactor SDK.

This module provides functions for fetching JWT tokens from the coordinator.
"""

from __future__ import annotations

import logging
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


# Default coordinator URL
PROD_COORDINATOR_URL = "https://api.reactor.inc"


async def fetch_jwt_token(
    api_key: str,
    coordinator_url: str = PROD_COORDINATOR_URL,
) -> str:
    """
    Fetch a JWT token from the coordinator using an API key.

    This is safe to use in Python applications (CLI tools, scripts, servers)
    since the API key is not exposed to end users like it would be in
    browser-based JavaScript applications.

    Args:
        api_key: Your Reactor API key.
        coordinator_url: Optional coordinator URL, defaults to production.

    Returns:
        The JWT token string.

    Raises:
        RuntimeError: If the token fetch fails.

    Example:
        >>> token = await fetch_jwt_token("your-api-key")
        >>> reactor = Reactor(model_name="my-model")
        >>> await reactor.connect(jwt_token=token)
    """
    url = f"{coordinator_url.rstrip('/')}/tokens"

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            headers={"X-API-Key": api_key},
        ) as response:
            if not response.ok:
                error_text = await response.text()
                raise RuntimeError(
                    f"Failed to fetch JWT token: {response.status} {error_text}"
                )

            data = await response.json()
            jwt_token: str = data["jwt"]

            logger.debug("Successfully fetched JWT token")
            return jwt_token

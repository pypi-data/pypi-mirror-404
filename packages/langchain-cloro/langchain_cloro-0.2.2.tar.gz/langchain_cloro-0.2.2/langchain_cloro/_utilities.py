"""Utilities for cloro integration."""

import os
from typing import Any

import httpx
from langchain_core.utils import convert_to_secret_str


def initialize_client(values: dict, *, timeout: float | None = None) -> dict:
    """Initialize the cloro HTTP client.

    Args:
        values: The values dictionary containing configuration.
        timeout: Request timeout in seconds. Default: None (no timeout).

    Returns:
        The updated values dictionary with initialized client.
    """
    cloro_api_key = values.get("cloro_api_key") or os.environ.get("CLORO_API_KEY") or ""
    values["cloro_api_key"] = convert_to_secret_str(cloro_api_key)

    # Initialize httpx client with appropriate settings
    # No timeout by default - requests will wait indefinitely
    values["client"] = httpx.Client(
        base_url="https://api.cloro.dev",
        headers={
            "Authorization": f"Bearer {values['cloro_api_key'].get_secret_value()}",
            "Content-Type": "application/json",
        },
        timeout=None,
    )
    return values


def build_monitor_params(
    prompt: str,
    country: str = "US",
    include: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build common monitoring parameters for AI endpoints.

    Args:
        prompt: The query/prompt string.
        country: ISO 3166-1 alpha-2 country code. Default: "US"
        include: Optional flags for additional response formats.
        **kwargs: Additional parameters to pass to the API.

    Returns:
        Dictionary of request parameters.
    """
    params = {
        "prompt": prompt,
        "country": country,
    }
    if include:
        params["include"] = include
    params.update(kwargs)
    return params


def build_google_search_params(
    query: str,
    country: str = "US",
    device: str = "desktop",
    pages: int = 1,
    include: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build parameters for Google Search endpoint.

    Args:
        query: The search query string.
        country: ISO 3166-1 alpha-2 country code. Default: "US"
        device: Device type (desktop or mobile). Default: "desktop"
        pages: Number of pages to scrape (1-20). Default: 1
        include: Optional flags for additional response formats.
        **kwargs: Additional parameters to pass to the API.

    Returns:
        Dictionary of request parameters.
    """
    params = {
        "query": query,
        "country": country,
        "device": device,
        "pages": pages,
    }
    if include:
        params["include"] = include
    params.update(kwargs)
    return params

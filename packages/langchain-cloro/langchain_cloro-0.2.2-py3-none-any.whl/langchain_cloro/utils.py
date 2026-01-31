"""Utility functions for cloro API."""

import httpx
from pydantic import SecretStr


def get_countries(
    cloro_api_key: str | SecretStr = "",
    model: str | None = None,
) -> list[str]:
    """Get list of supported country codes from cloro API.

    Args:
        cloro_api_key: The cloro API key. If not provided, uses CLORO_API_KEY env variable.
        model: Optional model name to filter countries (e.g., 'chatgpt', 'google', 'perplexity').
        timeout: Request timeout in seconds. Default: None (no timeout)

    Returns:
        List of ISO 3166-1 alpha-2 country codes.

    Raises:
        httpx.HTTPError: If the API request fails.
        ValueError: If the API key is not provided.

    Examples:
        Get all countries:
        >>> from langchain_cloro.utils import get_countries
        >>> countries = get_countries()

        Get countries for specific model:
        >>> countries = get_countries(model="chatgpt")
    """
    import os

    # Handle API key
    if isinstance(cloro_api_key, SecretStr):
        api_key_value = cloro_api_key.get_secret_value()
    else:
        api_key_value = cloro_api_key or os.environ.get("CLORO_API_KEY", "")

    if not api_key_value:
        msg = "cloro_api_key must be provided or set in CLORO_API_KEY environment variable"
        raise ValueError(msg)

    # Make request
    client = httpx.Client(
        base_url="https://api.cloro.dev",
        headers={
            "Authorization": f"Bearer {api_key_value}",
            "Content-Type": "application/json",
        },
        timeout=None,
    )

    try:
        params = {}
        if model:
            params["model"] = model

        response = client.get("/v1/countries", params=params)
        response.raise_for_status()
        return response.json()  # Returns list of country codes
    finally:
        client.close()

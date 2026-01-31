"""Tools for the cloro API monitoring endpoints."""

from __future__ import annotations

import json
from typing import Any, Union

import httpx
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import Field, SecretStr, model_validator

from langchain_cloro._utilities import (
    build_google_search_params,
    build_monitor_params,
    initialize_client,
)


class _CloroBaseTool(BaseTool):
    """Base class for cloro monitoring tools with common functionality."""

    client: Union[httpx.Client, Any] = Field(default=None)  # type: ignore[assignment]
    cloro_api_key: SecretStr = Field(default=SecretStr(""))
    timeout: float | None = Field(default=None, description="Request timeout in seconds")

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: dict) -> Any:
        """Validate the environment and initialize the client."""
        return initialize_client(values, timeout=values.get("timeout", 10.0))

    def _make_request(
        self, endpoint: str, params: dict[str, Any]
    ) -> str:
        """Make a request to the cloro API.

        Args:
            endpoint: The API endpoint path (e.g., "/v1/monitor/chatgpt").
            params: The request parameters.

        Returns:
            JSON string of the response or error message.
        """
        try:
            response = self.client.post(endpoint, json=params)
            response.raise_for_status()
            results = response.json()
            return json.dumps(results)
        except httpx.HTTPError as e:
            return json.dumps({"error": f"Error with cloro API: {e!s}"})
        except Exception as e:
            return json.dumps({"error": f"Unexpected error: {e!s}"})


class CloroGoogleSearch(_CloroBaseTool):
    r"""cloro Google Search tool.

    Extracts structured data from Google Search results, including organic results,
    People Also Ask questions, related searches, and optional AI Overview data.

    Setup:
        Install ``langchain-cloro`` and set environment variable ``CLORO_API_KEY``.

        .. code-block:: bash

            pip install -U langchain-cloro
            export CLORO_API_KEY="your-api-key"

    Instantiation:
        .. code-block:: python

            from langchain_cloro import CloroGoogleSearch

            tool = CloroGoogleSearch()

    Invocation:
        .. code-block:: python

            tool.invoke({"query": "best laptops for programming"})

    Include AI Overview:
        .. code-block:: python

            tool.invoke({
                "query": "best laptops for programming",
                "include_aioverview": True,
                "aioverview_markdown": True
            })
    """

    name: str = "cloro_google_search"
    description: str = (
        "A wrapper around cloro Google Search API. "
        "Extracts structured data from Google Search including organic results, "
        "People Also Ask, related searches, and optional AI Overview. "
        "Input should be a search query. "
        "Output is a JSON object with search results."
    )

    def _run(
        self,
        query: str,
        country: str = "US",
        device: str = "desktop",
        pages: int = 1,
        include_aioverview: bool = False,
        aioverview_markdown: bool = False,
        include_html: bool = False,
        run_manager: CallbackManagerForToolRun | None = None,
        **kwargs: Any,
    ) -> str:
        """Use the cloro Google Search tool.

        Args:
            query: The search query string.
            country: ISO 3166-1 alpha-2 country code. Default: "US"
            device: Device type (desktop or mobile). Default: "desktop"
            pages: Number of pages to scrape (1-20). Default: 1
            include_aioverview: Include Google AI Overview. Default: False
            aioverview_markdown: Format AI Overview as markdown. Default: False
            include_html: Include raw HTML response. Default: False
            run_manager: The run manager for callbacks.
            **kwargs: Additional parameters.

        Returns:
            JSON string of search results or error message.
        """
        include = {}
        if include_aioverview:
            include["aioverview"] = {"markdown": aioverview_markdown}
        if include_html:
            include["html"] = True

        params = build_google_search_params(
            query=query,
            country=country,
            device=device,
            pages=pages,
            include=include if include else None,
            **kwargs,
        )

        return self._make_request("/v1/monitor/google", params)


class CloroChatGPT(_CloroBaseTool):
    r"""cloro ChatGPT monitoring tool.

    Extracts structured data from ChatGPT with shopping cards, entity extraction,
    and advanced features for monitoring products, prices, and brand mentions.

    Setup:
        Install ``langchain-cloro`` and set environment variable ``CLORO_API_KEY``.

        .. code-block:: bash

            pip install -U langchain-cloro
            export CLORO_API_KEY="your-api-key"

    Instantiation:
        .. code-block:: python

            from langchain_cloro import CloroChatGPT

            tool = CloroChatGPT()

    Invocation:
        .. code-block:: python

            tool.invoke({"prompt": "What are the best sneakers under $100?"})
    """

    name: str = "cloro_chatgpt"
    description: str = (
        "A wrapper around cloro ChatGPT API. "
        "Extracts structured data from ChatGPT with shopping cards, entities, "
        "and sources. Useful for product monitoring, brand tracking, and "
        "e-commerce intelligence. "
        "Input should be a prompt. "
        "Output is a JSON object with the response and structured data."
    )

    def _run(
        self,
        prompt: str,
        country: str = "US",
        include_raw_response: bool = False,
        include_search_queries: bool = False,
        include_html: bool = False,
        include_markdown: bool = False,
        run_manager: CallbackManagerForToolRun | None = None,
        **kwargs: Any,
    ) -> str:
        """Use the cloro ChatGPT tool.

        Args:
            prompt: The prompt string.
            country: ISO 3166-1 alpha-2 country code. Default: "US"
            include_raw_response: Include raw streaming response events. Default: False
            include_search_queries: Include search fan-out queries. Default: False
            include_html: Include HTML response. Default: False
            include_markdown: Include markdown response. Default: False
            run_manager: The run manager for callbacks.
            **kwargs: Additional parameters.

        Returns:
            JSON string of the response or error message.
        """
        include = {}
        if include_raw_response:
            include["rawResponse"] = True
        if include_search_queries:
            include["searchQueries"] = True
        if include_html:
            include["html"] = True
        if include_markdown:
            include["markdown"] = True

        params = build_monitor_params(
            prompt=prompt,
            country=country,
            include=include if include else None,
            **kwargs,
        )

        return self._make_request("/v1/monitor/chatgpt", params)


class CloroGemini(_CloroBaseTool):
    r"""cloro Google Gemini monitoring tool.

    Extracts structured data from Google's Gemini AI with source citations,
    confidence levels, and multiple output formats.

    Setup:
        Install ``langchain-cloro`` and set environment variable ``CLORO_API_KEY``.

        .. code-block:: bash

            pip install -U langchain-cloro
            export CLORO_API_KEY="your-api-key"

    Instantiation:
        .. code-block:: python

            from langchain_cloro import CloroGemini

            tool = CloroGemini()

    Invocation:
        .. code-block:: python

            tool.invoke({"prompt": "Explain quantum entanglement"})
    """

    name: str = "cloro_gemini"
    description: str = (
        "A wrapper around cloro Google Gemini API. "
        "Extracts structured data from Gemini with source citations and "
        "confidence levels. Input should be a prompt. "
        "Output is a JSON object with the response and sources."
    )

    def _run(
        self,
        prompt: str,
        country: str = "US",
        include_html: bool = False,
        include_markdown: bool = False,
        run_manager: CallbackManagerForToolRun | None = None,
        **kwargs: Any,
    ) -> str:
        """Use the cloro Gemini tool.

        Args:
            prompt: The prompt string.
            country: ISO 3166-1 alpha-2 country code. Default: "US"
            include_html: Include HTML response. Default: False
            include_markdown: Include markdown response. Default: False
            run_manager: The run manager for callbacks.
            **kwargs: Additional parameters.

        Returns:
            JSON string of the response or error message.
        """
        include = {}
        if include_html:
            include["html"] = True
        if include_markdown:
            include["markdown"] = True

        params = build_monitor_params(
            prompt=prompt,
            country=country,
            include=include if include else None,
            **kwargs,
        )

        return self._make_request("/v1/monitor/gemini", params)


class CloroPerplexity(_CloroBaseTool):
    r"""cloro Perplexity monitoring tool.

    Extracts comprehensive structured data from Perplexity AI with real-time
    web sources, shopping products, media content, and travel information.

    Setup:
        Install ``langchain-cloro`` and set environment variable ``CLORO_API_KEY``.

        .. code-block:: bash

            pip install -U langchain-cloro
            export CLORO_API_KEY="your-api-key"

    Instantiation:
        .. code-block:: python

            from langchain_cloro import CloroPerplexity

            tool = CloroPerplexity()

    Invocation:
        .. code-block:: python

            tool.invoke({"prompt": "Best hotels in San Francisco"})
    """

    name: str = "cloro_perplexity"
    description: str = (
        "A wrapper around cloro Perplexity API. "
        "Extracts structured data from Perplexity with sources, shopping cards, "
        "media content, and travel information. "
        "Input should be a prompt. "
        "Output is a JSON object with the response and structured data."
    )

    def _run(
        self,
        prompt: str,
        country: str = "US",
        include_html: bool = False,
        include_markdown: bool = False,
        run_manager: CallbackManagerForToolRun | None = None,
        **kwargs: Any,
    ) -> str:
        """Use the cloro Perplexity tool.

        Args:
            prompt: The prompt string.
            country: ISO 3166-1 alpha-2 country code. Default: "US"
            include_html: Include HTML response. Default: False
            include_markdown: Include markdown response. Default: False
            run_manager: The run manager for callbacks.
            **kwargs: Additional parameters.

        Returns:
            JSON string of the response or error message.
        """
        include = {}
        if include_html:
            include["html"] = True
        if include_markdown:
            include["markdown"] = True

        params = build_monitor_params(
            prompt=prompt,
            country=country,
            include=include if include else None,
            **kwargs,
        )

        return self._make_request("/v1/monitor/perplexity", params)


class CloroGrok(_CloroBaseTool):
    r"""cloro Grok monitoring tool.

    Extracts comprehensive structured data from Grok with real-time web sources
    and enhanced source metadata including preview text, creator details, and images.

    Setup:
        Install ``langchain-cloro`` and set environment variable ``CLORO_API_KEY``.

        .. code-block:: bash

            pip install -U langchain-cloro
            export CLORO_API_KEY="your-api-key"

    Instantiation:
        .. code-block:: python

            from langchain_cloro import CloroGrok

            tool = CloroGrok()

    Invocation:
        .. code-block:: python

            tool.invoke({"prompt": "Latest news about AI"})
    """

    name: str = "cloro_grok"
    description: str = (
        "A wrapper around cloro Grok API. "
        "Extracts structured data from Grok with enhanced source metadata. "
        "Input should be a prompt. "
        "Output is a JSON object with the response and sources."
    )

    def _run(
        self,
        prompt: str,
        country: str = "US",
        include_html: bool = False,
        include_markdown: bool = False,
        run_manager: CallbackManagerForToolRun | None = None,
        **kwargs: Any,
    ) -> str:
        """Use the cloro Grok tool.

        Args:
            prompt: The prompt string.
            country: ISO 3166-1 alpha-2 country code. Default: "US"
            include_html: Include HTML response. Default: False
            include_markdown: Include markdown response. Default: False
            run_manager: The run manager for callbacks.
            **kwargs: Additional parameters.

        Returns:
            JSON string of the response or error message.
        """
        include = {}
        if include_html:
            include["html"] = True
        if include_markdown:
            include["markdown"] = True

        params = build_monitor_params(
            prompt=prompt,
            country=country,
            include=include if include else None,
            **kwargs,
        )

        return self._make_request("/v1/monitor/grok", params)


class CloroCopilot(_CloroBaseTool):
    r"""cloro Microsoft Copilot monitoring tool.

    Extracts structured data from Microsoft Copilot with source citations.

    Setup:
        Install ``langchain-cloro`` and set environment variable ``CLORO_API_KEY``.

        .. code-block:: bash

            pip install -U langchain-cloro
            export CLORO_API_KEY="your-api-key"

    Instantiation:
        .. code-block:: python

            from langchain_cloro import CloroCopilot

            tool = CloroCopilot()

    Invocation:
        .. code-block:: python

            tool.invoke({"prompt": "What is the capital of France?"})
    """

    name: str = "cloro_copilot"
    description: str = (
        "A wrapper around cloro Microsoft Copilot API. "
        "Extracts structured data from Copilot with source citations. "
        "Input should be a prompt. "
        "Output is a JSON object with the response and sources."
    )

    def _run(
        self,
        prompt: str,
        country: str = "US",
        include_html: bool = False,
        include_markdown: bool = False,
        run_manager: CallbackManagerForToolRun | None = None,
        **kwargs: Any,
    ) -> str:
        """Use the cloro Copilot tool.

        Args:
            prompt: The prompt string.
            country: ISO 3166-1 alpha-2 country code. Default: "US"
            include_html: Include HTML response. Default: False
            include_markdown: Include markdown response. Default: False
            run_manager: The run manager for callbacks.
            **kwargs: Additional parameters.

        Returns:
            JSON string of the response or error message.
        """
        include = {}
        if include_html:
            include["html"] = True
        if include_markdown:
            include["markdown"] = True

        params = build_monitor_params(
            prompt=prompt,
            country=country,
            include=include if include else None,
            **kwargs,
        )

        return self._make_request("/v1/monitor/copilot", params)


# Backwards compatibility aliases
CloroSearchRun = CloroGoogleSearch
CloroSearchResults = CloroGoogleSearch

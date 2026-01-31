"""LangChain integration tests for cloro tools.

This module contains integration tests required by LangChain for tool integrations.
These tests make actual API calls to verify the tools work correctly.

To run these tests:
1. Set the CLORO_API_KEY environment variable with a valid cloro API key
2. Run: pytest tests/integration_tests/test_tools.py

Example:
    export CLORO_API_KEY="your-api-key"
    pytest tests/integration_tests/test_tools.py -v

See https://docs.langchain.com/oss/python/contributing/standard-tests-langchain
"""

from __future__ import annotations

from typing import Any

import pytest
from langchain_tests.integration_tests import ToolsIntegrationTests

from langchain_cloro import (
    CloroChatGPT,
    CloroCopilot,
    CloroGemini,
    CloroGrok,
    CloroGoogleSearch,
    CloroPerplexity,
)


class TestCloroGoogleSearchIntegration(ToolsIntegrationTests):
    """LangChain integration tests for CloroGoogleSearch."""

    @property
    def tool_constructor(self) -> type[CloroGoogleSearch]:
        """Return the CloroGoogleSearch tool class."""
        return CloroGoogleSearch

    @property
    def tool_constructor_params(self) -> dict[str, Any]:
        """Return parameters for tool construction.

        Uses CLORO_API_KEY from environment variable.
        """
        return {}

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        """Return example parameters for tool invocation."""
        return {"query": "best laptops for programming"}


class TestCloroChatGPTIntegration(ToolsIntegrationTests):
    """LangChain integration tests for CloroChatGPT."""

    @property
    def tool_constructor(self) -> type[CloroChatGPT]:
        """Return the CloroChatGPT tool class."""
        return CloroChatGPT

    @property
    def tool_constructor_params(self) -> dict[str, Any]:
        """Return parameters for tool construction.

        Uses CLORO_API_KEY from environment variable.
        """
        return {}

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        """Return example parameters for tool invocation."""
        return {"prompt": "What are the best sneakers under $100?"}


class TestCloroGeminiIntegration(ToolsIntegrationTests):
    """LangChain integration tests for CloroGemini."""

    @property
    def tool_constructor(self) -> type[CloroGemini]:
        """Return the CloroGemini tool class."""
        return CloroGemini

    @property
    def tool_constructor_params(self) -> dict[str, Any]:
        """Return parameters for tool construction.

        Uses CLORO_API_KEY from environment variable.
        """
        return {}

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        """Return example parameters for tool invocation."""
        return {"prompt": "Explain quantum entanglement"}


class TestCloroPerplexityIntegration(ToolsIntegrationTests):
    """LangChain integration tests for CloroPerplexity."""

    @property
    def tool_constructor(self) -> type[CloroPerplexity]:
        """Return the CloroPerplexity tool class."""
        return CloroPerplexity

    @property
    def tool_constructor_params(self) -> dict[str, Any]:
        """Return parameters for tool construction.

        Uses CLORO_API_KEY from environment variable.
        """
        return {}

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        """Return example parameters for tool invocation."""
        return {"prompt": "Best hotels in San Francisco"}


class TestCloroGrokIntegration(ToolsIntegrationTests):
    """LangChain integration tests for CloroGrok."""

    @property
    def tool_constructor(self) -> type[CloroGrok]:
        """Return the CloroGrok tool class."""
        return CloroGrok

    @property
    def tool_constructor_params(self) -> dict[str, Any]:
        """Return parameters for tool construction.

        Uses CLORO_API_KEY from environment variable.
        """
        return {}

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        """Return example parameters for tool invocation."""
        return {"prompt": "Latest news about AI"}


class TestCloroCopilotIntegration(ToolsIntegrationTests):
    """LangChain integration tests for CloroCopilot."""

    @property
    def tool_constructor(self) -> type[CloroCopilot]:
        """Return the CloroCopilot tool class."""
        return CloroCopilot

    @property
    def tool_constructor_params(self) -> dict[str, Any]:
        """Return parameters for tool construction.

        Uses CLORO_API_KEY from environment variable.
        """
        return {}

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        """Return example parameters for tool invocation."""
        return {"prompt": "What is the capital of France?"}

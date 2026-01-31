"""LangChain standard tests for cloro tools.

This module contains standard tests required by LangChain for tool integrations.
See https://docs.langchain.com/oss/python/contributing/standard-tests-langchain
"""

from __future__ import annotations

from typing import Any
from unittest import mock

import pytest
from langchain_tests.unit_tests.tools import ToolsUnitTests

from langchain_cloro import (
    CloroChatGPT,
    CloroCopilot,
    CloroGemini,
    CloroGrok,
    CloroGoogleSearch,
    CloroPerplexity,
)


class TestCloroGoogleSearchStandard(ToolsUnitTests):
    """LangChain standard tests for CloroGoogleSearch."""

    @property
    def tool_constructor(self) -> type[CloroGoogleSearch]:
        """Return the CloroGoogleSearch tool class."""
        return CloroGoogleSearch

    @property
    def tool_constructor_params(self) -> dict[str, Any]:
        """Return parameters for tool construction."""
        return {
            "cloro_api_key": "test-api-key",
        }

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        """Return example parameters for tool invocation."""
        return {"query": "test query"}

    @property
    def init_from_env_params(
        self,
    ) -> tuple[dict[str, str], dict[str, Any], dict[str, Any]]:
        """Return params for environment variable initialization test."""
        return (
            {"CLORO_API_KEY": "env-api-key"},
            {},
            {"cloro_api_key": "env-api-key"},
        )


class TestCloroChatGPTStandard(ToolsUnitTests):
    """LangChain standard tests for CloroChatGPT."""

    @property
    def tool_constructor(self) -> type[CloroChatGPT]:
        """Return the CloroChatGPT tool class."""
        return CloroChatGPT

    @property
    def tool_constructor_params(self) -> dict[str, Any]:
        """Return parameters for tool construction."""
        return {
            "cloro_api_key": "test-api-key",
        }

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        """Return example parameters for tool invocation."""
        return {"prompt": "test prompt"}

    @property
    def init_from_env_params(
        self,
    ) -> tuple[dict[str, str], dict[str, Any], dict[str, Any]]:
        """Return params for environment variable initialization test."""
        return (
            {"CLORO_API_KEY": "env-api-key"},
            {},
            {"cloro_api_key": "env-api-key"},
        )


class TestCloroGeminiStandard(ToolsUnitTests):
    """LangChain standard tests for CloroGemini."""

    @property
    def tool_constructor(self) -> type[CloroGemini]:
        """Return the CloroGemini tool class."""
        return CloroGemini

    @property
    def tool_constructor_params(self) -> dict[str, Any]:
        """Return parameters for tool construction."""
        return {
            "cloro_api_key": "test-api-key",
        }

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        """Return example parameters for tool invocation."""
        return {"prompt": "test prompt"}

    @property
    def init_from_env_params(
        self,
    ) -> tuple[dict[str, str], dict[str, Any], dict[str, Any]]:
        """Return params for environment variable initialization test."""
        return (
            {"CLORO_API_KEY": "env-api-key"},
            {},
            {"cloro_api_key": "env-api-key"},
        )


class TestCloroPerplexityStandard(ToolsUnitTests):
    """LangChain standard tests for CloroPerplexity."""

    @property
    def tool_constructor(self) -> type[CloroPerplexity]:
        """Return the CloroPerplexity tool class."""
        return CloroPerplexity

    @property
    def tool_constructor_params(self) -> dict[str, Any]:
        """Return parameters for tool construction."""
        return {
            "cloro_api_key": "test-api-key",
        }

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        """Return example parameters for tool invocation."""
        return {"prompt": "test prompt"}

    @property
    def init_from_env_params(
        self,
    ) -> tuple[dict[str, str], dict[str, Any], dict[str, Any]]:
        """Return params for environment variable initialization test."""
        return (
            {"CLORO_API_KEY": "env-api-key"},
            {},
            {"cloro_api_key": "env-api-key"},
        )


class TestCloroGrokStandard(ToolsUnitTests):
    """LangChain standard tests for CloroGrok."""

    @property
    def tool_constructor(self) -> type[CloroGrok]:
        """Return the CloroGrok tool class."""
        return CloroGrok

    @property
    def tool_constructor_params(self) -> dict[str, Any]:
        """Return parameters for tool construction."""
        return {
            "cloro_api_key": "test-api-key",
        }

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        """Return example parameters for tool invocation."""
        return {"prompt": "test prompt"}

    @property
    def init_from_env_params(
        self,
    ) -> tuple[dict[str, str], dict[str, Any], dict[str, Any]]:
        """Return params for environment variable initialization test."""
        return (
            {"CLORO_API_KEY": "env-api-key"},
            {},
            {"cloro_api_key": "env-api-key"},
        )


class TestCloroCopilotStandard(ToolsUnitTests):
    """LangChain standard tests for CloroCopilot."""

    @property
    def tool_constructor(self) -> type[CloroCopilot]:
        """Return the CloroCopilot tool class."""
        return CloroCopilot

    @property
    def tool_constructor_params(self) -> dict[str, Any]:
        """Return parameters for tool construction."""
        return {
            "cloro_api_key": "test-api-key",
        }

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        """Return example parameters for tool invocation."""
        return {"prompt": "test prompt"}

    @property
    def init_from_env_params(
        self,
    ) -> tuple[dict[str, str], dict[str, Any], dict[str, Any]]:
        """Return params for environment variable initialization test."""
        return (
            {"CLORO_API_KEY": "env-api-key"},
            {},
            {"cloro_api_key": "env-api-key"},
        )

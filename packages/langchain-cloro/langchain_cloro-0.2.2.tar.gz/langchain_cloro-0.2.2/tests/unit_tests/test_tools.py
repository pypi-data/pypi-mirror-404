"""Unit tests for cloro tools."""

from unittest.mock import MagicMock, patch

import pytest
from langchain_cloro.tools import (
    CloroChatGPT,
    CloroCopilot,
    CloroGemini,
    CloroGrok,
    CloroGoogleSearch,
    CloroPerplexity,
)


class TestCloroGoogleSearch:
    """Test CloroGoogleSearch tool."""

    @patch("langchain_cloro.tools.initialize_client")
    def test_initialization_with_api_key(self, mock_init: MagicMock) -> None:
        """Test initialization with API key."""
        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": MagicMock(),
        }

        tool = CloroGoogleSearch(cloro_api_key="test-api-key")

        assert tool.name == "cloro_google_search"
        assert "Google Search" in tool.description
        mock_init.assert_called_once()

    @patch("langchain_cloro.tools.initialize_client")
    def test_run_success(self, mock_init: MagicMock) -> None:
        """Test successful search execution."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "result": {"organicResults": []}}
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": mock_client,
        }

        tool = CloroGoogleSearch(cloro_api_key="test-api-key")
        result = tool._run(query="test query")

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/monitor/google"
        assert "params" not in call_args[1]  # Uses json instead
        assert call_args[1]["json"]["query"] == "test query"

    @patch("langchain_cloro.tools.initialize_client")
    def test_run_with_aioverview(self, mock_init: MagicMock) -> None:
        """Test search with AI Overview."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": mock_client,
        }

        tool = CloroGoogleSearch(cloro_api_key="test-api-key")
        result = tool._run(query="test query", include_aioverview=True, aioverview_markdown=True)

        call_args = mock_client.post.call_args
        assert "include" in call_args[1]["json"]
        assert "aioverview" in call_args[1]["json"]["include"]
        assert call_args[1]["json"]["include"]["aioverview"]["markdown"] is True


class TestCloroChatGPT:
    """Test CloroChatGPT tool."""

    @patch("langchain_cloro.tools.initialize_client")
    def test_run_success(self, mock_init: MagicMock) -> None:
        """Test successful ChatGPT execution."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "result": {"text": "Response"}}
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": mock_client,
        }

        tool = CloroChatGPT(cloro_api_key="test-api-key")
        result = tool._run(prompt="test prompt")

        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/monitor/chatgpt"
        assert call_args[1]["json"]["prompt"] == "test prompt"

    @patch("langchain_cloro.tools.initialize_client")
    def test_run_with_shopping_options(self, mock_init: MagicMock) -> None:
        """Test ChatGPT with shopping card options."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": mock_client,
        }

        tool = CloroChatGPT(cloro_api_key="test-api-key")
        result = tool._run(
            prompt="test prompt",
            include_raw_response=True,
            include_search_queries=True,
        )

        call_args = mock_client.post.call_args
        assert "include" in call_args[1]["json"]
        assert call_args[1]["json"]["include"]["rawResponse"] is True
        assert call_args[1]["json"]["include"]["searchQueries"] is True


class TestCloroGemini:
    """Test CloroGemini tool."""

    @patch("langchain_cloro.tools.initialize_client")
    def test_run_success(self, mock_init: MagicMock) -> None:
        """Test successful Gemini execution."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "result": {"text": "Response"}}
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": mock_client,
        }

        tool = CloroGemini(cloro_api_key="test-api-key")
        result = tool._run(prompt="test prompt")

        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/monitor/gemini"
        assert call_args[1]["json"]["prompt"] == "test prompt"


class TestCloroPerplexity:
    """Test CloroPerplexity tool."""

    @patch("langchain_cloro.tools.initialize_client")
    def test_run_success(self, mock_init: MagicMock) -> None:
        """Test successful Perplexity execution."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "result": {"text": "Response"}}
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": mock_client,
        }

        tool = CloroPerplexity(cloro_api_key="test-api-key")
        result = tool._run(prompt="test prompt")

        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/monitor/perplexity"
        assert call_args[1]["json"]["prompt"] == "test prompt"


class TestCloroGrok:
    """Test CloroGrok tool."""

    @patch("langchain_cloro.tools.initialize_client")
    def test_run_success(self, mock_init: MagicMock) -> None:
        """Test successful Grok execution."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "result": {"text": "Response"}}
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": mock_client,
        }

        tool = CloroGrok(cloro_api_key="test-api-key")
        result = tool._run(prompt="test prompt")

        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/monitor/grok"
        assert call_args[1]["json"]["prompt"] == "test prompt"


class TestCloroCopilot:
    """Test CloroCopilot tool."""

    @patch("langchain_cloro.tools.initialize_client")
    def test_run_success(self, mock_init: MagicMock) -> None:
        """Test successful Copilot execution."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "result": {"text": "Response"}}
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": mock_client,
        }

        tool = CloroCopilot(cloro_api_key="test-api-key")
        result = tool._run(prompt="test prompt")

        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/monitor/copilot"
        assert call_args[1]["json"]["prompt"] == "test prompt"


class TestBaseToolErrorHandling:
    """Test base tool error handling."""

    @patch("langchain_cloro.tools.initialize_client")
    def test_http_error_handling(self, mock_init: MagicMock) -> None:
        """Test HTTP error is handled gracefully."""
        import httpx

        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=MagicMock()
        )

        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": mock_client,
        }

        tool = CloroGoogleSearch(cloro_api_key="test-api-key")
        result = tool._run(query="test query")

        assert "Error with cloro API" in result

    @patch("langchain_cloro.tools.initialize_client")
    def test_unexpected_error_handling(self, mock_init: MagicMock) -> None:
        """Test unexpected error is handled gracefully."""
        mock_client = MagicMock()
        mock_client.post.side_effect = Exception("Unexpected error")

        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": mock_client,
        }

        tool = CloroChatGPT(cloro_api_key="test-api-key")
        result = tool._run(prompt="test prompt")

        assert "Unexpected error" in result

"""Tests for AgentGram client."""

import pytest
from unittest.mock import Mock, patch

from agentgram import AgentGram, AsyncAgentGram
from agentgram.exceptions import AuthenticationError


class TestAgentGramClient:
    """Test synchronous AgentGram client."""

    def test_initialization(self):
        """Test client initialization."""
        client = AgentGram(api_key="ag_test")
        assert client._http.api_key == "ag_test"
        assert client._http.base_url == "https://agentgram.co/api/v1"
        client.close()

    def test_custom_base_url(self):
        """Test client with custom base URL."""
        client = AgentGram(
            api_key="ag_test",
            base_url="https://custom.com/api/v1",
        )
        assert client._http.base_url == "https://custom.com/api/v1"
        client.close()

    @patch("agentgram.http.httpx.Client")
    def test_health_check(self, mock_client):
        """Test health check endpoint."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "status": "ok",
            "version": "1.0.0",
        }
        mock_client.return_value.request.return_value = mock_response

        client = AgentGram(api_key="ag_test")
        status = client.health()

        assert status.status == "ok"
        assert status.version == "1.0.0"
        client.close()

    @patch("agentgram.http.httpx.Client")
    def test_me_endpoint(self, mock_client):
        """Test getting current agent profile."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": "agent-123",
            "name": "TestAgent",
            "karma": 42,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        mock_client.return_value.request.return_value = mock_response

        client = AgentGram(api_key="ag_test")
        me = client.me()

        assert me.id == "agent-123"
        assert me.name == "TestAgent"
        assert me.karma == 42
        client.close()

    def test_context_manager(self):
        """Test client as context manager."""
        with AgentGram(api_key="ag_test") as client:
            assert client._http.api_key == "ag_test"


class TestAsyncAgentGramClient:
    """Test asynchronous AgentGram client."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test async client initialization."""
        client = AsyncAgentGram(api_key="ag_test")
        assert client._http.api_key == "ag_test"
        assert client._http.base_url == "https://agentgram.co/api/v1"
        await client.close()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async client as context manager."""
        async with AsyncAgentGram(api_key="ag_test") as client:
            assert client._http.api_key == "ag_test"

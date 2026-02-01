"""Test the OMXClient core functionality."""
import pytest
import os
from unittest.mock import AsyncMock, patch
from omx_sdk import OMXClient


class TestOMXClient:
    """Test cases for OMXClient."""

    def test_client_initialization_with_params(self):
        """Test client initialization with explicit parameters."""
        client = OMXClient(client_id="test-client", secret_key="test-secret")
        assert client.client_id == "test-client"
        assert client.secret_key == "test-secret"
        assert client.base_url == "https://blhilidnsybhfdmwqsrx.supabase.co/functions/v1"

    def test_client_initialization_with_env_vars(self):
        """Test client initialization with environment variables."""
        with patch.dict(os.environ, {'OMX_CLIENT_ID': 'env-client', 'OMX_SECRET_KEY': 'env-secret'}):
            client = OMXClient()
            assert client.client_id == "env-client"
            assert client.secret_key == "env-secret"

    def test_client_initialization_missing_credentials(self):
        """Test client initialization fails without credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="client_id and secret_key are required"):
                OMXClient()

    def test_client_custom_base_url(self):
        """Test client initialization with custom base URL."""
        client = OMXClient(
            client_id="test-client", 
            secret_key="test-secret",
            base_url="https://custom.api.com"
        )
        assert client.base_url == "https://custom.api.com"

    def test_managers_initialized(self):
        """Test that all managers are properly initialized."""
        client = OMXClient(client_id="test-client", secret_key="test-secret")
        assert hasattr(client, 'notification')
        assert hasattr(client, 'email')
        assert hasattr(client, 'geo_trigger')
        assert hasattr(client, 'beacon')
        assert hasattr(client, 'webhook')
        assert hasattr(client, 'campaign')
        assert hasattr(client, 'workflow')
        assert hasattr(client, 'analytics')
        assert hasattr(client, 'segment')
        assert hasattr(client, 'events')

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client as async context manager."""
        async with OMXClient(client_id="test-client", secret_key="test-secret") as client:
            assert client.client_id == "test-client"
        # Client should be closed after context exit
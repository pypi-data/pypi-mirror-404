"""
Basic tests for Nemati AI SDK.
"""

import pytest
from nemati import NematiAI
from nemati._exceptions import AuthenticationError


def test_client_requires_api_key():
    """Test that client requires API key."""
    with pytest.raises(AuthenticationError):
        NematiAI(api_key=None)


def test_client_validates_api_key_format():
    """Test that client validates API key format."""
    with pytest.raises(AuthenticationError):
        NematiAI(api_key="invalid_key")


def test_client_accepts_valid_api_key(api_key):
    """Test that client accepts valid API key."""
    client = NematiAI(api_key=api_key)
    assert client is not None
    assert client._config.api_key == api_key
    client.close()


def test_client_detects_test_key(api_key):
    """Test that client detects test API key."""
    client = NematiAI(api_key=api_key)
    assert client.is_test_mode is True
    client.close()


def test_client_has_all_resources(api_key):
    """Test that client has all expected resources."""
    client = NematiAI(api_key=api_key)
    
    assert hasattr(client, 'chat')
    assert hasattr(client, 'writer')
    assert hasattr(client, 'image')
    assert hasattr(client, 'audio')
    assert hasattr(client, 'trends')
    assert hasattr(client, 'market')
    assert hasattr(client, 'documents')
    assert hasattr(client, 'account')
    
    client.close()


def test_client_context_manager(api_key):
    """Test that client works as context manager."""
    with NematiAI(api_key=api_key) as client:
        assert client is not None

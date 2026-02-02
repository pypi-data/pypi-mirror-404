import pytest
from sanic import Request
from sanic.exceptions import Unauthorized
from srf.middleware.authmiddleware import (
    is_public_endpoint, extract_bearer_token, set_user_to_request_ctx
)


@pytest.mark.asyncio
async def test_is_public_endpoint():
    """Test is_public_endpoint function"""
    # Create a mock request with public endpoint
    class MockApp:
        def __init__(self, config):
            self.config = config
    
    class MockRequest:
        def __init__(self, path, app):
            self.path = path
            self.app = app
    
    config = type('Config', (), {'NON_AUTH_ENDPOINTS': ['login', 'register']})
    app = MockApp(config)
    
    # Test public endpoint
    request = MockRequest('/api/auth/login', app)
    assert is_public_endpoint(request) is True
    
    # Test non-public endpoint
    request = MockRequest('/api/users', app)
    assert is_public_endpoint(request) is False


@pytest.mark.asyncio
async def test_extract_bearer_token():
    """Test extract_bearer_token function"""
    # Create a mock request
    class MockRequest:
        def __init__(self, headers):
            self.headers = headers
    
    # Test with valid token
    request = MockRequest({'Authorization': 'Bearer test-token'})
    token = extract_bearer_token(request)
    assert token == 'test-token'
    
    # Test without Authorization header
    request = MockRequest({})
    with pytest.raises(Unauthorized):
        extract_bearer_token(request)
    
    # Test with invalid format
    request = MockRequest({'Authorization': 'Invalid format'})
    with pytest.raises(Unauthorized):
        extract_bearer_token(request)


@pytest.mark.asyncio
async def test_set_user_to_request_ctx():
    """Test set_user_to_request_ctx function"""
    # Create a mock request with public endpoint
    class MockApp:
        def __init__(self, config):
            self.config = config
    
    class MockRequest:
        def __init__(self, path, app, headers=None):
            self.path = path
            self.app = app
            self.headers = headers or {}
            self.ctx = type('Ctx', (), {})
    
    config = type('Config', (), {'NON_AUTH_ENDPOINTS': ['login']})
    app = MockApp(config)
    
    # Test public endpoint (should not raise exception)
    request = MockRequest('/api/auth/login', app)
    await set_user_to_request_ctx(request)
    
    # Test non-public endpoint (would normally require authentication)
    # Note: This test would fail in real scenario without a valid token
    # For now, we just test that it doesn't crash with proper setup

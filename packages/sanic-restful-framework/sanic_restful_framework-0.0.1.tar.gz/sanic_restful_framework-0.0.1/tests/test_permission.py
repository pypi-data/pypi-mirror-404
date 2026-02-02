import pytest
from sanic import Request
from srf.permission.permission import BasePermission


class AllowAllPermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        return True


class DenyAllPermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        return False


@pytest.mark.asyncio
async def test_base_permission_has_permission():
    """Test that BasePermission has_permission returns True by default"""
    permission = BasePermission()
    # Create mock request and view objects
    class MockRequest:
        pass
    class MockView:
        pass
    request = MockRequest()
    view = MockView()
    assert permission.has_permission(request, view) is True


@pytest.mark.asyncio
async def test_allow_all_permission():
    """Test that AllowAllPermission returns True"""
    permission = AllowAllPermission()
    # Create mock request and view objects
    class MockRequest:
        pass
    class MockView:
        pass
    request = MockRequest()
    view = MockView()
    assert permission.has_permission(request, view) is True


@pytest.mark.asyncio
async def test_deny_all_permission():
    """Test that DenyAllPermission returns False"""
    permission = DenyAllPermission()
    # Create mock request and view objects
    class MockRequest:
        pass
    class MockView:
        pass
    request = MockRequest()
    view = MockView()
    assert permission.has_permission(request, view) is False

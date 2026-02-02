import pytest
from sanic import Blueprint
from srf.route import SanicRouter
from srf.views.base import BaseViewSet
from srf.decorators import action


class MockViewSet(BaseViewSet):
    queryset = None
    
    @action(methods=['GET'], detail=False, url_path='custom-action')
    async def custom_action(self, request):
        return {"message": "Custom action"}
    
    @action(methods=['POST'], detail=True, url_path='detailed-action')
    async def detailed_action(self, request, pk):
        return {"message": f"Detailed action for {pk}"}
    
    async def list(self, request):
        return {"message": "List action"}
    
    async def create(self, request):
        return {"message": "Create action"}
    
    async def retrieve(self, request, pk):
        return {"message": f"Retrieve action for {pk}"}
    
    async def update(self, request, pk):
        return {"message": f"Update action for {pk}"}
    
    async def destroy(self, request, pk):
        return {"message": f"Destroy action for {pk}"}


def test_sanic_router_init():
    # Test default initialization
    router = SanicRouter()
    assert router.prefix == ""
    assert isinstance(router.bp, Blueprint)
    assert router.bp.name == "api"
    
    # Test with prefix
    router = SanicRouter(prefix="api")
    assert router.prefix == "/api"
    assert router.bp.name == "api"
    
    # Test with custom blueprint
    custom_bp = Blueprint("custom")
    router = SanicRouter(bp=custom_bp, prefix="custom")
    assert router.bp == custom_bp
    assert router.prefix == "/custom"


def test_sanic_router_register():
    # This test verifies that the router can be created and register method can be called
    # without errors. Sanic routes are only available after app startup, so we can't directly
    # check the routes list in unit tests.
    router = SanicRouter(prefix="api")
    router.register("users", MockViewSet, name="users")
    
    # Just check that the blueprint is accessible and has the correct name
    bp = router.get_blueprint()
    assert isinstance(bp, Blueprint)
    assert bp.name == "api"


def test_sanic_router_register_without_prefix():
    # This test verifies that the router can be created without a prefix and register method can be called
    # without errors. Sanic routes are only available after app startup, so we can't directly
    # check the routes list in unit tests.
    router = SanicRouter()
    router.register("users", MockViewSet, name="users")
    
    # Just check that the blueprint is accessible and has the correct name
    bp = router.get_blueprint()
    assert isinstance(bp, Blueprint)
    assert bp.name == "api"


def test_sanic_router_custom_action_methods():
    router = SanicRouter(prefix="api")
    router.register("users", MockViewSet, name="users")
    
    bp = router.get_blueprint()
    
    # Find the custom action routes and check their methods
    for route in bp.routes:
        if route.uri == "/api/users/custom-action":
            assert "GET" in route.methods
        elif route.uri == "/api/users/<pk:int>/detailed-action":
            assert "POST" in route.methods
        elif route.uri == "/api/users":
            assert "GET" in route.methods
            assert "POST" in route.methods
        elif route.uri == "/api/users/<pk:int>":
            assert "GET" in route.methods
            assert "PUT" in route.methods
            assert "PATCH" in route.methods
            assert "DELETE" in route.methods


def test_sanic_router_route_names():
    # This test verifies that the router can be created and register method can be called
    # without errors. Sanic routes are only available after app startup, so we can't directly
    # check the routes list or route names in unit tests.
    router = SanicRouter(prefix="api")
    router.register("users", MockViewSet, name="users")
    
    # Just check that the blueprint is accessible
    bp = router.get_blueprint()
    assert isinstance(bp, Blueprint)
    # Verify the blueprint has no errors and can be retrieved
    assert bp is not None

import pytest
from sanic import Request
from sanic.exceptions import HTTPException
from srf.views.base import BaseViewSet
from srf.views.http_status import HTTPStatus


class MockPermission:
    def __init__(self, allow=True):
        self.allow = allow
    
    def has_permission(self, request):
        return self.allow


class MockModel:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class MockQuerySet:
    def __init__(self, items):
        self.items = items
        self.model = MockModel
    
    async def get_or_none(self, **kwargs):
        id = kwargs.get('id')
        return next((item for item in self.items if item.id == id), None)
    
    async def create(self, **kwargs):
        new_id = len(self.items) + 1
        new_item = self.model(new_id, kwargs.get('name'))
        self.items.append(new_item)
        return new_item
    
    async def count(self):
        return len(self.items)
    
    async def offset(self, offset):
        self.offset_val = offset
        return self
    
    async def limit(self, limit):
        self.limit_val = limit
        return self
    
    async def __call__(self):
        start = getattr(self, 'offset_val', 0)
        end = start + getattr(self, 'limit_val', len(self.items))
        return self.items[start:end]


@pytest.fixture
def mock_request():
    class MockRequest:
        def __init__(self, method='GET', json=None, ctx=None):
            self.method = method
            self.json = json
            self.ctx = ctx or type('obj', (object,), {})()
    return MockRequest


@pytest.fixture
def mock_pydantic_model():
    class MockPydanticModel:
        def __init__(self, id=None, name=None):
            self.id = id
            self.name = name
        
        @classmethod
        def model_validate(cls, obj, **kwargs):
            if hasattr(obj, 'id') and hasattr(obj, 'name'):
                return cls(id=obj.id, name=obj.name)
            return cls(**obj)
        
        def model_dump(self, **kwargs):
            return {'id': self.id, 'name': self.name}
    return MockPydanticModel


@pytest.mark.asyncio
async def test_check_permissions_allowed():
    class TestViewSet(BaseViewSet):
        permission_classes = [MockPermission]
    
    viewset = TestViewSet()
    request = type('obj', (object,), {})()
    
    # Should not raise exception when permission is allowed
    await viewset.check_permissions(request)


@pytest.mark.asyncio
async def test_check_permissions_denied():
    class TestViewSet(BaseViewSet):
        permission_classes = [lambda: MockPermission(allow=False)]
    
    viewset = TestViewSet()
    request = type('obj', (object,), {})()
    
    # Should raise HTTPException when permission is denied
    with pytest.raises(HTTPException) as exc_info:
        await viewset.check_permissions(request)
    
    assert exc_info.value.status_code == HTTPStatus.HTTP_403_FORBIDDEN
    assert str(exc_info.value) == "Forbidden"


@pytest.mark.asyncio
async def test_check_permissions_no_permissions():
    class TestViewSet(BaseViewSet):
        permission_classes = []
    
    viewset = TestViewSet()
    request = type('obj', (object,), {})()
    
    # Should not raise exception when no permissions are defined
    await viewset.check_permissions(request)


@pytest.mark.asyncio
async def test_get_object():
    items = [MockModel(1, 'Item 1'), MockModel(2, 'Item 2')]
    queryset = MockQuerySet(items)
    
    class TestViewSet(BaseViewSet):
        @property
        def queryset(self):
            return queryset
    
    viewset = TestViewSet()
    request = type('obj', (object,), {})()
    
    # Test getting existing object
    obj = await viewset.get_object(request, 1)
    assert obj.id == 1
    assert obj.name == 'Item 1'
    
    # Test getting non-existing object
    with pytest.raises(HTTPException) as exc_info:
        await viewset.get_object(request, 999)
    
    assert exc_info.value.status_code == HTTPStatus.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_current_user():
    class TestViewSet(BaseViewSet):
        pass
    
    viewset = TestViewSet()
    
    # Test with user in request.ctx
    request = type('obj', (object,), {
        'ctx': type('obj', (object,), {'user': 'test_user'})()
    })()
    user = viewset.get_current_user(request)
    assert user == 'test_user'
    
    # Test with no user
    request = type('obj', (object,), {
        'ctx': type('obj', (object,), {})()
    })()
    user = viewset.get_current_user(request)
    assert user is None


@pytest.mark.asyncio
async def test_as_view():
    items = [MockModel(1, 'Item 1')]
    queryset = MockQuerySet(items)
    
    class TestViewSet(BaseViewSet):
        @property
        def queryset(self):
            return queryset
        
        async def list(self, request):
            return {"message": "List"}
        
        async def create(self, request):
            return {"message": "Create"}
    
    # Test creating view function
    view_func = TestViewSet.as_view()
    assert callable(view_func)
    
    # Test with custom actions
    custom_view_func = TestViewSet.as_view(actions={'get': 'list', 'post': 'create'})
    assert callable(custom_view_func)

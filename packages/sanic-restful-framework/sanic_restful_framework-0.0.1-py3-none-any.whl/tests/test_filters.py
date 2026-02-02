import pytest
from sanic import Request
from sanic.views import HTTPMethodView
from srf.filters.filter import (
    BaseFilter, SearchFilter, JsonLogicFilter, QueryParamFilter, OrderingFactory
)


class TestView(HTTPMethodView):
    search_fields = ['name', 'description']
    filter_fields = {'name': 'name', 'age': 'age'}
    ordering_fields = ['name', 'age']


@pytest.mark.asyncio
async def test_base_filter_subclass():
    """Test that BaseFilter can be subclassed"""
    class TestFilter(BaseFilter):
        @property
        def filter_params(self):
            return "test"
        
        def filter_queryset(self, request, queryset):
            return queryset
    
    view = TestView()
    filter_instance = TestFilter(view)
    assert filter_instance.view_class == view
    assert filter_instance.filter_params == "test"


@pytest.mark.asyncio
async def test_search_filter_get_search_terms():
    """Test SearchFilter get_search_terms method"""
    view = TestView()
    search_filter = SearchFilter(view)
    
    # Create a mock request with search parameter
    class MockRequest:
        def __init__(self, args):
            self.args = args
        
        def get(self, key, default=None):
            return self.args.get(key, default)
    
    request = MockRequest({'search': 'test'})
    terms = search_filter.get_search_terms(request)
    assert terms == ['test']


@pytest.mark.asyncio
async def test_json_logic_filter_filter_queryset():
    """Test JsonLogicFilter filter_queryset method"""
    view = TestView()
    json_filter = JsonLogicFilter(view)
    
    # Create a mock request with filter parameter
    class MockRequest:
        def __init__(self, args):
            self.args = args
    
    # Create a mock queryset
    class MockQuerySet:
        def filter(self, *args, **kwargs):
            return self
    
    request = MockRequest({'filter': '{"==": [{"var": "name"}, "test"]}'})
    queryset = MockQuerySet()
    result = json_filter.filter_queryset(request, queryset)
    assert result == queryset


@pytest.mark.asyncio
async def test_query_param_filter_filter_queryset():
    """Test QueryParamFilter filter_queryset method"""
    view = TestView()
    param_filter = QueryParamFilter(view)
    
    # Create a mock request with filter parameters
    class MockArgs:
        def __init__(self, data):
            self.data = data
        
        def getlist(self, key):
            return self.data.get(key, [])
        
        def keys(self):
            return self.data.keys()
    
    class MockRequest:
        def __init__(self, args):
            self.args = MockArgs(args)
    
    # Create a mock queryset
    class MockQuerySet:
        def filter(self, *args, **kwargs):
            return self
    
    request = MockRequest({'name': ['test'], 'age': ['25']})
    queryset = MockQuerySet()
    result = param_filter.filter_queryset(request, queryset)
    assert result == queryset


@pytest.mark.asyncio
async def test_ordering_factory_filter_queryset():
    """Test OrderingFactory filter_queryset method"""
    view = TestView()
    ordering_factory = OrderingFactory(view)
    
    # Create a mock request with sort parameter
    class MockRequest:
        def __init__(self, args):
            self.args = args
        
        def get(self, key, default=None):
            return self.args.get(key, default)
    
    # Create a mock queryset
    class MockQuerySet:
        def order_by(self, *args):
            return self
    
    request = MockRequest({'sort': 'name,-age'})
    queryset = MockQuerySet()
    result = ordering_factory.filter_queryset(request, queryset)
    assert result == queryset

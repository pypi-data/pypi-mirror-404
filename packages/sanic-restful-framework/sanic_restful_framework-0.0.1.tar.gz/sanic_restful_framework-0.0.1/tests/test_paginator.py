import pytest
from sanic import Request
from tortoise.queryset import QuerySet
from srf.paginator import PaginationHandler, PaginationParams, PaginationResult


from pydantic import BaseModel


class MockModel(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True


class MockQuerySet(QuerySet):
    def __init__(self, items):
        self.items = items
        self.model = type('obj', (), {'__name__': 'MockModel'})()
    
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
        def __init__(self, args=None):
            self.args = args or {}
    return MockRequest


@pytest.mark.asyncio
async def test_pagination_handler_init():
    items = [MockModel(id=i, name=f'Item {i}') for i in range(20)]
    queryset = MockQuerySet(items)
    
    # Test default initialization
    paginator = PaginationHandler(queryset)
    assert paginator.page == 1
    assert paginator.page_size == 10
    assert paginator.max_page_size == 100
    
    # Test custom initialization
    paginator = PaginationHandler(queryset, page=2, page_size=20, max_page_size=200)
    assert paginator.page == 2
    assert paginator.page_size == 20
    assert paginator.max_page_size == 200


@pytest.mark.asyncio
async def test_pagination_handler_from_queryset(mock_request):
    items = [MockModel(id=i, name=f'Item {i}') for i in range(20)]
    queryset = MockQuerySet(items)
    
    # Test with default parameters
    request = mock_request()
    paginator = PaginationHandler.from_queryset(queryset, request)
    assert paginator.page == 1
    assert paginator.page_size == 10
    
    # Test with custom page
    request = mock_request({'page': '3'})
    paginator = PaginationHandler.from_queryset(queryset, request)
    assert paginator.page == 3
    
    # Test with custom page_size
    request = mock_request({'page_size': '20'})
    paginator = PaginationHandler.from_queryset(queryset, request)
    assert paginator.page_size == 20
    
    # Test with page_size exceeding max_page_size
    request = mock_request({'page_size': '150'})
    paginator = PaginationHandler.from_queryset(queryset, request)
    assert paginator.page_size == 100
    
    # Test with invalid page parameter
    request = mock_request({'page': 'invalid'})
    paginator = PaginationHandler.from_queryset(queryset, request)
    assert paginator.page == 1


@pytest.mark.asyncio
async def test_paginate():
    items = [MockModel(id=i, name=f'Item {i}') for i in range(25)]
    queryset = MockQuerySet(items)
    
    # Test first page
    paginator = PaginationHandler(queryset, page=1, page_size=10)
    result = await paginator.paginate(sch_model=MockModel)
    assert isinstance(result, PaginationResult)
    assert result.count == 25
    assert result.previous is False
    assert result.next is True
    assert len(result.results) == 10
    
    # Test second page
    paginator = PaginationHandler(queryset, page=2, page_size=10)
    result = await paginator.paginate(sch_model=MockModel)
    assert result.previous is True
    assert result.next is True
    assert len(result.results) == 10
    
    # Test last page
    paginator = PaginationHandler(queryset, page=3, page_size=10)
    result = await paginator.paginate(sch_model=MockModel)
    assert result.previous is True
    assert result.next is False
    assert len(result.results) == 5


@pytest.mark.asyncio
async def test_to_dict():
    items = [MockModel(id=i, name=f'Item {i}') for i in range(20)]
    queryset = MockQuerySet(items)
    
    paginator = PaginationHandler(queryset)
    result_dict = await paginator.to_dict(sch_model=MockModel)
    
    assert isinstance(result_dict, dict)
    assert 'count' in result_dict
    assert 'results' in result_dict
    assert 'next' in result_dict
    assert 'previous' in result_dict
    assert result_dict['count'] == 20
    assert len(result_dict['results']) == 10


def test_num_pages():
    paginator = PaginationHandler(MockQuerySet([]))
    
    # Test with zero items
    assert paginator.num_pages(0) == 0
    
    # Test with items less than page size
    assert paginator.num_pages(5) == 1
    
    # Test with items equal to page size
    assert paginator.num_pages(10) == 1
    
    # Test with items more than page size
    assert paginator.num_pages(25) == 3
    
    # Test with custom page size
    paginator = PaginationHandler(MockQuerySet([]), page_size=20)
    assert paginator.num_pages(25) == 2

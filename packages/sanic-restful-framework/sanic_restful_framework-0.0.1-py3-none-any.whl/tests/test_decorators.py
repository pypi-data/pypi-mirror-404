import pytest
from srf.decorators import action


@pytest.mark.asyncio
async def test_action_decorator():
    """Test action decorator"""
    # Test with default parameters
    @action()
    def test_action(self):
        pass
    
    assert hasattr(test_action, 'extra_info')
    assert test_action.extra_info['methods'] == ['get']
    assert test_action.extra_info['detail'] is None
    assert test_action.extra_info['url_path'] == '/test_action'
    assert test_action.extra_info['url_name'] == 'test_action'


@pytest.mark.asyncio
async def test_action_decorator_with_custom_parameters():
    """Test action decorator with custom parameters"""
    @action(
        methods=['post', 'put'],
        detail=True,
        url_path='custom-path',
        url_name='custom-name',
        custom_param='value'
    )
    def test_action(self):
        pass
    
    assert hasattr(test_action, 'extra_info')
    assert test_action.extra_info['methods'] == ['post', 'put']
    assert test_action.extra_info['detail'] is True
    assert test_action.extra_info['url_path'] == 'custom-path'
    assert test_action.extra_info['url_name'] == 'custom-name'
    assert test_action.extra_info['custom_param'] == 'value'


@pytest.mark.asyncio
async def test_action_decorator_invalid_detail():
    """Test action decorator with invalid detail parameter"""
    with pytest.raises(TypeError):
        @action(detail='not a boolean')
        def test_action(self):
            pass

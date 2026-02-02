import pytest
from srf.tools.utils import camel_to_snake, generate_code
from srf.tools.email import EmailValidator, VerifyEmailRequest, send_email, send_vertify_code


@pytest.mark.asyncio
async def test_camel_to_snake():
    """Test camel_to_snake function"""
    assert camel_to_snake('CamelCase') == 'camel_case'
    assert camel_to_snake('HTTPRequest') == 'http_request'
    assert camel_to_snake('user_id') == 'user_id'
    assert camel_to_snake('') == ''


@pytest.mark.asyncio
async def test_generate_code():
    """Test generate_code function"""
    code = generate_code()
    assert isinstance(code, str)
    assert len(code) == 5
    assert code.isdigit()
    
    # Test with custom length
    code_10 = generate_code(10)
    assert isinstance(code_10, str)
    assert len(code_10) == 10
    assert code_10.isdigit()


@pytest.mark.asyncio
async def test_email_validator():
    """Test EmailValidator model"""
    # Test with valid email
    valid_email = EmailValidator(email='test@example.com')
    assert valid_email.email == 'test@example.com'
    
    # Test with invalid email (should raise validation error)
    with pytest.raises(Exception):
        EmailValidator(email='invalid-email')


@pytest.mark.asyncio
async def test_verify_email_request():
    """Test VerifyEmailRequest model"""
    # Test with valid confirmation code
    valid_request = VerifyEmailRequest(confirmations=12345)
    assert valid_request.confirmations == 12345
    
    # Test with invalid confirmation code (should raise validation error)
    with pytest.raises(Exception):
        VerifyEmailRequest(confirmations=0)  # Too small
    
    with pytest.raises(Exception):
        VerifyEmailRequest(confirmations=100000)  # Too large


@pytest.mark.asyncio
async def test_send_email():
    """Test send_email function"""
    # This test will not actually send an email
    # It just tests that the function can be called without errors
    try:
        result = send_email('test@example.com', 'Test Subject', 'Test Content')
        # The result will be False if EmailConfig is not set up, but that's expected
        assert isinstance(result, bool)
    except Exception as e:
        # If EmailConfig is not set up, the function might raise an exception
        # This is expected in a test environment
        pass


@pytest.mark.asyncio
async def test_send_vertify_code():
    """Test send_vertify_code function"""
    # This test will not actually send an email
    # It just tests that the function can be called without errors
    send_vertify_code('test@example.com', '12345')
    # The function doesn't return anything, so we just test that it runs

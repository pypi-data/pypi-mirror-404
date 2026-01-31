from userverse_python_client.response_messages import Errors


def test_invalid_request_error_values():
    err = Errors.INVALID_REQUEST.value
    assert err.code == "invalid_request"
    assert "invalid" in err.message.lower()

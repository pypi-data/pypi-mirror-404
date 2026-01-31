import base64

from userverse_python_client import UverseUserClient
from userverse_models.user.user import UserCreateModel, UserLoginModel, UserUpdateModel


def _basic_auth(email: str, password: str) -> str:
    encoded = base64.b64encode(f"{email}:{password}".encode("utf-8")).decode("utf-8")
    return f"Basic {encoded}"


def test_encode_basic_auth():
    client = UverseUserClient("https://example.test")
    assert client._encode_basic_auth("a@example.com", "pw") == _basic_auth(
        "a@example.com", "pw"
    )


def test_user_login_uses_basic_auth_and_patch():
    client = UverseUserClient("https://example.test")
    login = UserLoginModel(email="a@example.com", password="pw")

    def fake_request(method, path, headers=None, **_kwargs):
        assert method == "PATCH"
        assert path == "/user/login"
        assert headers == {"Authorization": _basic_auth("a@example.com", "pw")}
        return {"data": {"token": "abc"}}

    client._request = fake_request
    assert client.user_login(login) == {"data": {"token": "abc"}}


def test_user_login_requires_data_key():
    client = UverseUserClient("https://example.test")
    login = UserLoginModel(email="a@example.com", password="pw")
    client._request = lambda *_args, **_kwargs: {}
    try:
        client.user_login(login)
    except ValueError as exc:
        assert "Invalid response" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_create_user_posts_with_basic_auth():
    client = UverseUserClient("https://example.test")
    login = UserLoginModel(email="a@example.com", password="pw")
    user_data = UserCreateModel(email="a@example.com", password="pw", name="Ada")

    def fake_request(method, path, json=None, headers=None, **_kwargs):
        assert method == "POST"
        assert path == "/user"
        assert json == user_data
        assert headers == {"Authorization": _basic_auth("a@example.com", "pw")}
        return {"data": {"id": "1"}}

    client._request = fake_request
    assert client.create_user(user_data, login) == {"data": {"id": "1"}}


def test_create_user_requires_data_dict():
    client = UverseUserClient("https://example.test")
    login = UserLoginModel(email="a@example.com", password="pw")
    user_data = UserCreateModel(email="a@example.com", password="pw")
    client._request = lambda *_args, **_kwargs: {"data": "oops"}
    try:
        client.create_user(user_data, login)
    except ValueError as exc:
        assert "Expected user data" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_get_user_fetches_current_user():
    client = UverseUserClient("https://example.test")

    def fake_request(method, path, **_kwargs):
        assert method == "GET"
        assert path == "/user/get"
        return {"data": {"id": "1"}}

    client._request = fake_request
    assert client.get_user() == {"data": {"id": "1"}}


def test_update_user_patches_current_user():
    client = UverseUserClient("https://example.test")
    user_update = UserUpdateModel(name="Ada")

    def fake_request(method, path, json=None, **_kwargs):
        assert method == "PATCH"
        assert path == "/user/update"
        assert json == user_update
        return {"data": {"name": "Ada"}}

    client._request = fake_request
    assert client.update_user(user_update) == {"data": {"name": "Ada"}}


def test_resend_verification_email_posts():
    client = UverseUserClient("https://example.test")

    def fake_request(method, path, **_kwargs):
        assert method == "POST"
        assert path == "/user/resend-verification"
        return {"data": None}

    client._request = fake_request
    assert client.resend_verification_email() == {"data": None}


def test_verify_user_uses_token_query():
    client = UverseUserClient("https://example.test")

    def fake_request(method, path, **_kwargs):
        assert method == "GET"
        assert path == "/user/verify?token=abc"
        return {"data": None}

    client._request = fake_request
    assert client.verify_user("abc") == {"data": None}


def test_request_password_reset_uses_email_query():
    client = UverseUserClient("https://example.test")

    def fake_request(method, path, **_kwargs):
        assert method == "PATCH"
        assert path == "/password-reset/request?email=a@example.com"
        return {"data": None}

    client._request = fake_request
    assert client.request_password_reset("a@example.com") == {"data": None}


def test_reset_password_validate_otp_uses_basic_auth_and_payload():
    client = UverseUserClient("https://example.test")
    login = UserLoginModel(email="a@example.com", password="pw")

    def fake_request(method, path, json=None, headers=None, **_kwargs):
        assert method == "PATCH"
        assert path == "/password-reset/validate-otp"
        assert json == {"one_time_pin": "123"}
        assert headers == {"Authorization": _basic_auth("a@example.com", "pw")}
        return {"data": None}

    client._request = fake_request
    assert client.reset_password_validate_otp(login, "123") == {"data": None}

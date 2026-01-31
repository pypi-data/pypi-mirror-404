import pytest

from userverse_python_client.clients.company_user_management import (
    UverseCompanyUserManagementClient,
)
from userverse_models.company.user import CompanyUserAddModel
from userverse_models.user.user import UserQueryParams


def _client() -> UverseCompanyUserManagementClient:
    return UverseCompanyUserManagementClient(
        "https://example.test", access_token="token"
    )


def test_add_user_to_company_posts_payload() -> None:
    client = _client()
    add_model = CompanyUserAddModel(user_id=5, role_name="admin")
    called: dict[str, object] = {}

    def fake_request(method, path, json=None, **_kwargs):
        called.update(method=method, path=path, json=json)
        return {"data": {"id": 1, "user_id": 5}}

    client._request = fake_request  # type: ignore[method-assign]
    response = client.add_user_to_company(company_id=10, user_data=add_model)

    assert called == {
        "method": "POST",
        "path": "/company/10/users",
        "json": add_model.model_dump(exclude_none=True),
    }
    assert response["data"]["user_id"] == 5


def test_add_user_to_company_requires_dict_payload() -> None:
    client = _client()
    add_model = CompanyUserAddModel(user_id=5)

    def fake_request(*_args, **_kwargs):
        return {"data": []}

    client._request = fake_request  # type: ignore[method-assign]
    with pytest.raises(ValueError, match="Expected company user data"):
        client.add_user_to_company(1, add_model)


def test_delete_user_from_company_calls_endpoint() -> None:
    client = _client()
    called: dict[str, object] = {}

    def fake_request(method, path, **_kwargs):
        called.update(method=method, path=path)
        return {"data": None}

    client._request = fake_request  # type: ignore[method-assign]
    response = client.delete_user_from_company(company_id=7, user_id=3)

    assert called == {"method": "DELETE", "path": "/company/7/users/3"}
    assert response["data"] is None


def test_delete_user_from_company_requires_response_body() -> None:
    client = _client()

    def fake_request(*_args, **_kwargs):
        return None

    client._request = fake_request  # type: ignore[method-assign]
    with pytest.raises(ValueError, match="Invalid response"):
        client.delete_user_from_company(1, 2)


def test_list_company_users_calls_endpoint() -> None:
    client = _client()
    params = UserQueryParams(limit=25, page=2)
    called: dict[str, object] = {}

    def fake_request(method, path, params=None, **_kwargs):
        called.update(method=method, path=path, params=params)
        return {
            "data": {
                "records": [{"user_id": 9}],
                "pagination": {"limit": 25, "current_page": 2},
            }
        }

    client._request = fake_request  # type: ignore[method-assign]
    response = client.list_company_users(company_id=11, query_params=params)

    assert called == {
        "method": "GET",
        "path": "/company/11/users",
        "params": params.model_dump(exclude_none=True),
    }
    assert response["data"]["records"][0]["user_id"] == 9


def test_list_company_users_requires_dict_payload() -> None:
    client = _client()
    params = UserQueryParams()

    def fake_request(*_args, **_kwargs):
        return {"data": []}

    client._request = fake_request  # type: ignore[method-assign]
    with pytest.raises(ValueError, match="Expected company user pagination data"):
        client.list_company_users(1, params)

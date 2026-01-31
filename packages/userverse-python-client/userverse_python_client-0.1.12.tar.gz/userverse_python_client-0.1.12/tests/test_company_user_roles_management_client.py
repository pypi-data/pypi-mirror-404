import pytest

from userverse_python_client.clients.company_user_roles_management import (
    UverseCompanyUserRolesManagement,
)
from userverse_models.company.roles import (
    RoleCreateModel,
    RoleUpdateModel,
    RoleDeleteModel,
    RoleQueryParamsModel,
    CompanyDefaultRoles,
)


def _client() -> UverseCompanyUserRolesManagement:
    return UverseCompanyUserRolesManagement("https://example.test", access_token="tok")


def test_get_company_roles_calls_endpoint() -> None:
    client = _client()
    params = RoleQueryParamsModel(limit=5, name="Viewer")
    called: dict[str, object] = {}

    def fake_request(method, path, params=None, **_kwargs):
        called.update(method=method, path=path, params=params)
        return {
            "data": {
                "records": [{"name": "Viewer"}],
                "pagination": {"limit": 5, "current_page": 1},
            }
        }

    client._request = fake_request  # type: ignore[method-assign]
    response = client.get_company_roles(company_id=3, query_params=params)

    assert called == {
        "method": "GET",
        "path": "/company/3/roles",
        "params": params.model_dump(exclude_none=True),
    }
    assert response["data"]["records"][0]["name"] == "Viewer"


def test_get_company_roles_requires_dict_payload() -> None:
    client = _client()
    params = RoleQueryParamsModel()

    def fake_request(*_args, **_kwargs):
        return {"data": []}

    client._request = fake_request  # type: ignore[method-assign]
    with pytest.raises(ValueError, match="role pagination data"):
        client.get_company_roles(1, params)


def test_create_company_role_posts_payload() -> None:
    client = _client()
    role = RoleCreateModel(name="Editor", description="Edit access")
    called: dict[str, object] = {}

    def fake_request(method, path, json=None, **_kwargs):
        called.update(method=method, path=path, json=json)
        return {"data": {"name": "Editor"}}

    client._request = fake_request  # type: ignore[method-assign]
    response = client.create_company_role(2, role)

    assert called == {
        "method": "POST",
        "path": "/company/2/roles",
        "json": role.model_dump(exclude_none=True),
    }
    assert response["data"]["name"] == "Editor"


def test_create_company_role_requires_dict_payload() -> None:
    client = _client()
    role = RoleCreateModel(name="Editor")

    def fake_request(*_args, **_kwargs):
        return {"data": []}

    client._request = fake_request  # type: ignore[method-assign]
    with pytest.raises(ValueError, match="Expected role data"):
        client.create_company_role(2, role)


def test_update_company_role_puts_payload() -> None:
    client = _client()
    role = RoleUpdateModel(description="Read-only")
    called: dict[str, object] = {}

    def fake_request(method, path, json=None, **_kwargs):
        called.update(method=method, path=path, json=json)
        return {"data": {"name": "Viewer", "description": "Read-only"}}

    client._request = fake_request  # type: ignore[method-assign]
    response = client.update_company_role(5, "Viewer", role)

    assert called == {
        "method": "PUT",
        "path": "/company/5/roles/Viewer",
        "json": role.model_dump(exclude_none=True),
    }
    assert response["data"]["description"] == "Read-only"


def test_update_company_role_requires_dict_payload() -> None:
    client = _client()
    role = RoleUpdateModel(description="Nope")

    def fake_request(*_args, **_kwargs):
        return {"data": []}

    client._request = fake_request  # type: ignore[method-assign]
    with pytest.raises(ValueError, match="Expected role data"):
        client.update_company_role(1, "Viewer", role)


def test_delete_company_role_sends_payload() -> None:
    client = _client()
    delete_model = RoleDeleteModel(
        replacement_role_name="Viewer", role_name_to_delete="Editor"
    )
    called: dict[str, object] = {}

    def fake_request(method, path, json=None, **_kwargs):
        called.update(method=method, path=path, json=json)
        return {"data": {"status": "ok"}}

    client._request = fake_request  # type: ignore[method-assign]
    response = client.delete_company_role(8, delete_model)

    assert called == {
        "method": "DELETE",
        "path": "/company/8/roles",
        "json": delete_model.model_dump(exclude_none=True),
    }
    assert response["data"]["status"] == "ok"


def test_delete_company_role_requires_dict_payload() -> None:
    client = _client()
    delete_model = RoleDeleteModel(
        replacement_role_name="Viewer", role_name_to_delete="Editor"
    )

    def fake_request(*_args, **_kwargs):
        return {"data": []}

    client._request = fake_request  # type: ignore[method-assign]
    with pytest.raises(ValueError, match="Expected response data"):
        client.delete_company_role(1, delete_model)


def test_list_default_roles_returns_names() -> None:
    roles = UverseCompanyUserRolesManagement.list_default_roles()

    assert "Administrator" in roles
    assert all(isinstance(role, str) for role in roles)

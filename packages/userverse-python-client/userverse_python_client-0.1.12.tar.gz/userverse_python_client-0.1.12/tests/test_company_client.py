import pytest

from userverse_python_client.clients.company import UverseCompanyClient
from userverse_models.company.company import (
    CompanyCreateModel,
    CompanyUpdateModel,
    CompanyQueryParamsModel,
)


def _client() -> UverseCompanyClient:
    return UverseCompanyClient("https://example.test", access_token="token")


def test_get_user_companies_calls_endpoint() -> None:
    client = _client()
    params = CompanyQueryParamsModel(limit=5, name="Acme")
    called = {}

    def fake_request(method, path, params=None, **_kwargs):
        called.update(method=method, path=path, params=params)
        return {
            "data": {
                "records": [{"name": "Acme"}],
                "pagination": {
                    "total_records": 1,
                    "limit": 5,
                    "current_page": 1,
                    "total_pages": 1,
                },
            }
        }

    client._request = fake_request  # type: ignore[method-assign]
    response = client.get_user_companies(params)

    assert called == {
        "method": "GET",
        "path": "/user/companies",
        "params": params.model_dump(exclude_none=True),
    }
    assert response["data"]["records"][0]["name"] == "Acme"


def test_get_user_companies_requires_dict_payload() -> None:
    client = _client()

    def fake_request(*_args, **_kwargs):
        return {"data": []}

    client._request = fake_request  # type: ignore[method-assign]
    with pytest.raises(ValueError, match="pagination data"):
        client.get_user_companies()


def test_get_company_by_id_calls_endpoint() -> None:
    client = _client()
    called = {}

    def fake_request(method, path, **_kwargs):
        called.update(method=method, path=path)
        return {"data": {"id": 1}}

    client._request = fake_request  # type: ignore[method-assign]
    response = client.get_company_by_id_or_email(company_id=7)

    assert called == {"method": "GET", "path": "/company?company_id=7"}
    assert response["data"]["id"] == 1


def test_get_company_by_email_calls_endpoint() -> None:
    client = _client()
    called = {}

    def fake_request(method, path, **_kwargs):
        called.update(method=method, path=path)
        return {"data": {"id": 2, "name": "Acme"}}

    client._request = fake_request  # type: ignore[method-assign]
    response = client.get_company_by_id_or_email(email="owner@example.com")

    assert called == {"method": "GET", "path": "/company?email=owner@example.com"}
    assert response["data"]["name"] == "Acme"


def test_get_company_requires_identifier() -> None:
    client = _client()
    with pytest.raises(ValueError, match="must be provided"):
        client.get_company_by_id_or_email()


def test_update_company_calls_patch_with_payload() -> None:
    client = _client()
    company_update = CompanyUpdateModel(name="Updated")
    called = {}

    def fake_request(method, path, json=None, **_kwargs):
        called.update(method=method, path=path, json=json)
        return {"data": {"id": 3, "name": "Updated"}}

    client._request = fake_request  # type: ignore[method-assign]
    response = client.update_company(3, company_update)

    assert called == {
        "method": "PATCH",
        "path": "/company/3",
        "json": company_update.model_dump(exclude_none=True),
    }
    assert response["data"]["name"] == "Updated"


def test_update_company_requires_dict_payload() -> None:
    client = _client()
    update = CompanyUpdateModel(name="Nope")

    def fake_request(*_args, **_kwargs):
        return {"data": []}

    client._request = fake_request  # type: ignore[method-assign]
    with pytest.raises(ValueError, match="Expected company data"):
        client.update_company(1, update)


def test_create_company_posts_payload() -> None:
    client = _client()
    create = CompanyCreateModel(name="New", email="info@example.com")
    called = {}

    def fake_request(method, path, json=None, **_kwargs):
        called.update(method=method, path=path, json=json)
        return {"data": {"id": 10, "name": "New"}}

    client._request = fake_request  # type: ignore[method-assign]
    response = client.create_company(create)

    assert called == {
        "method": "POST",
        "path": "/company",
        "json": create.model_dump(exclude_none=True),
    }
    assert response["data"]["id"] == 10


def test_create_company_requires_dict_payload() -> None:
    client = _client()
    create = CompanyCreateModel(name="New", email="info@example.com")

    def fake_request(*_args, **_kwargs):
        return {"data": []}

    client._request = fake_request  # type: ignore[method-assign]
    with pytest.raises(ValueError, match="Expected company data"):
        client.create_company(create)

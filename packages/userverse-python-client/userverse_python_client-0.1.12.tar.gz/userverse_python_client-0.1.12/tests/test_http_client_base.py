import requests
from dataclasses import dataclass

from userverse_python_client.error_model import ClientErrorModel
from userverse_python_client.http_client_base import BaseClient


class FakeResponse:
    def __init__(self, status_code=200, content=b"{}", json_data=None, text=""):
        self.status_code = status_code
        self.content = content
        self._json_data = json_data
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            http_err = requests.exceptions.HTTPError("HTTP error")
            http_err.response = self
            raise http_err

    def json(self):
        return self._json_data


def test_request_rejects_relative_path():
    client = BaseClient("https://example.test")
    try:
        client._request("GET", "user")
    except ValueError as exc:
        assert "Path must start" in str(exc)
    else:
        raise AssertionError("Expected ValueError for relative path")


def test_request_returns_json():
    client = BaseClient("https://example.test")

    def fake_request(**_kwargs):
        return FakeResponse(json_data={"ok": True})

    client.session.request = fake_request
    assert client._request("GET", "/health") == {"ok": True}


def test_request_returns_none_for_empty_content():
    client = BaseClient("https://example.test")

    def fake_request(**_kwargs):
        return FakeResponse(content=b"", json_data=None)

    client.session.request = fake_request
    assert client._request("GET", "/health") is None


def test_request_wraps_http_error_with_detail_payload():
    client = BaseClient("https://example.test")

    def fake_request(**_kwargs):
        return FakeResponse(
            status_code=400,
            content=b'{"detail": {"message": "Nope", "error": "bad"}}',
            json_data={"detail": {"message": "Nope", "error": "bad"}},
        )

    client.session.request = fake_request
    try:
        client._request("GET", "/broken")
    except ClientErrorModel as exc:
        assert exc.status_code == 400
        assert "Nope" in str(exc)
        assert "bad" in str(exc)
    else:
        raise AssertionError("Expected ClientErrorModel")


def test_request_wraps_http_error_without_detail_payload():
    client = BaseClient("https://example.test")

    def fake_request(**_kwargs):
        return FakeResponse(
            status_code=500,
            content=b"oops",
            json_data="oops",
            text="oops",
        )

    client.session.request = fake_request
    try:
        client._request("GET", "/broken")
    except ClientErrorModel as exc:
        assert exc.status_code == 500
        assert "invalid" in str(exc).lower()
    else:
        raise AssertionError("Expected ClientErrorModel")


def test_request_wraps_request_exception():
    client = BaseClient("https://example.test")

    def fake_request(**_kwargs):
        raise requests.exceptions.RequestException("boom")

    client.session.request = fake_request
    try:
        client._request("GET", "/broken")
    except ClientErrorModel as exc:
        assert exc.status_code == 500
        assert "boom" in str(exc)
    else:
        raise AssertionError("Expected ClientErrorModel")


def test_set_access_token_sets_bearer_header():
    client = BaseClient("https://example.test")
    client.set_access_token("abc123")
    assert client.session.headers["Authorization"] == "bearer abc123"


def test_build_path_with_query_handles_sequences_and_none():
    path = BaseClient._build_path_with_query(
        "/company", {"company_id": 1, "tags": ["a", "b"], "skip": None}
    )
    assert path == "/company?company_id=1&tags=a&tags=b"


def test_build_path_with_query_without_params_returns_original():
    assert BaseClient._build_path_with_query("/plain", None) == "/plain"


@dataclass
class _DataPayload:
    name: str


class _ModelPayload:
    def model_dump(self, **kwargs):
        assert kwargs == {"exclude_none": True}
        return {"model": "dumped"}


class _DictPayload:
    def dict(self):
        return {"dict": "payload"}


def test_prepare_json_payload_serializes_various_inputs():
    assert BaseClient._prepare_json_payload(None) is None
    assert BaseClient._prepare_json_payload({"raw": True}) == {"raw": True}
    assert BaseClient._prepare_json_payload(_DataPayload("Ada")) == {"name": "Ada"}
    assert BaseClient._prepare_json_payload(_ModelPayload()) == {"model": "dumped"}
    assert BaseClient._prepare_json_payload(_DictPayload()) == {"dict": "payload"}


def test_request_serializes_json_payload_before_dispatch():
    client = BaseClient("https://example.test")
    sent = {}

    class _Payload:
        def model_dump(self, **_kwargs):
            return {"key": "value"}

    def fake_request(**kwargs):
        sent.update(kwargs)
        return FakeResponse(json_data={"ok": True})

    client.session.request = fake_request
    assert client._request("POST", "/with-json", json=_Payload()) == {"ok": True}
    assert sent["json"] == {"key": "value"}

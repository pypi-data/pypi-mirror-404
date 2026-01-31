from userverse_python_client.error_model import ClientErrorModel
from sverse_generic_models.app_error import AppErrorResponseModel, DetailModel


def test_app_client_error_includes_detail_error():
    payload = AppErrorResponseModel(
        detail=DetailModel(message="Bad request", error="missing")
    )
    err = ClientErrorModel(status_code=400, payload=payload)
    assert err.status_code == 400
    assert err.payload == payload
    assert "Bad request" in str(err)
    assert "missing" in str(err)


def test_app_client_error_without_detail_error():
    payload = AppErrorResponseModel(
        detail=DetailModel(message="Bad request", error=None)
    )
    err = ClientErrorModel(status_code=400, payload=payload)
    assert "Bad request" == str(err)

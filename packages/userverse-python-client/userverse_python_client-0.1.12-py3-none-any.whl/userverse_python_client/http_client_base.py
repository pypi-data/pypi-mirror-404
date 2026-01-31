import requests
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Optional

from sverse_generic_models.app_error import AppErrorResponseModel, DetailModel
from .error_model import ClientErrorModel
from .response_messages import Errors


class BaseClient:
    def __init__(
        self,
        base_url: str,
        access_token: Optional[str] = None,
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )
        self.timeout = timeout

        if access_token:
            self.set_access_token(access_token)

    def set_access_token(self, token: str) -> None:
        # API expects lower-case bearer scheme to match historical behavior tested downstream
        self.session.headers["Authorization"] = f"bearer {token}"

    @staticmethod
    def _build_path_with_query(path: str, params: Optional[Dict[str, Any]]) -> str:
        if not params:
            return path
        query_parts = []
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    query_parts.append(f"{key}={item}")
            else:
                query_parts.append(f"{key}={value}")

        if not query_parts:
            return path
        return f"{path}?{'&'.join(str(part) for part in query_parts)}"

    @staticmethod
    def _prepare_json_payload(payload: Optional[Any]) -> Optional[Any]:
        if payload is None:
            return None
        if isinstance(payload, dict):
            return payload
        if is_dataclass(payload):
            return asdict(payload)

        for attr in ("model_dump", "dict"):
            method = getattr(payload, attr, None)
            if callable(method):
                try:
                    return method(exclude_none=True)
                except TypeError:
                    return method()

        return payload

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        if not path.startswith("/"):
            raise ValueError("Path must start with '/'")

        url = f"{self.base_url}{path}"
        prepared_json = self._prepare_json_payload(json)

        try:
            resp = self.session.request(
                method=method,
                url=url,
                params=params,
                json=prepared_json,
                headers=headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()

            # If API can return empty body (204 etc.), guard it:
            if not resp.content:
                return None

            try:
                return resp.json()
            except ValueError:
                return resp.text

        except requests.exceptions.HTTPError as http_err:
            status = http_err.response.status_code if http_err.response else 500

            err_def = Errors.INVALID_REQUEST.value
            payload = None

            if http_err.response is not None and http_err.response.content:
                try:
                    server_error = http_err.response.json()
                except ValueError:
                    server_error = http_err.response.text

                if isinstance(server_error, dict) and "detail" in server_error:
                    detail = server_error.get("detail")
                    if isinstance(detail, dict):
                        payload = AppErrorResponseModel(
                            detail=DetailModel(
                                message=detail.get("message", err_def.message),
                                error=str(detail.get("error", "No content")),
                            )
                        )
                if payload is None:
                    payload = AppErrorResponseModel(
                        detail=DetailModel(
                            message=err_def.message,
                            error=str(server_error),
                        )
                    )

            if payload is None:
                payload = AppErrorResponseModel(
                    detail=DetailModel(
                        message=err_def.message,
                        error="No content",
                    )
                )

            raise ClientErrorModel(status_code=status, payload=payload) from http_err

        except requests.exceptions.RequestException as req_err:
            # timeouts, DNS, connection errors, etc.
            err_def = Errors.INVALID_REQUEST.value
            payload = AppErrorResponseModel(
                detail=DetailModel(
                    message=err_def.message,
                    error=str(req_err),
                )
            )
            raise ClientErrorModel(status_code=500, payload=payload) from req_err

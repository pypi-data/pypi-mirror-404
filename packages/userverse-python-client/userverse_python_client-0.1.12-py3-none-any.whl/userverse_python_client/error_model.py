from sverse_generic_models.app_error import AppErrorResponseModel


class ClientErrorModel(Exception):
    def __init__(self, status_code: int, payload: AppErrorResponseModel):
        self.status_code = status_code
        self.payload = payload
        detail_error = getattr(payload.detail, "error", None)
        message = payload.detail.message
        if detail_error:
            message = f"{message} (details: {detail_error})"
        super().__init__(message)

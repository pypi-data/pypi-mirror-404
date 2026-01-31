from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Error:
    code: str
    message: str


class Errors(Enum):
    INVALID_REQUEST = Error(
        code="invalid_request",
        message="The request was invalid. Please check your input and try again.",
    )

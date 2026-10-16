from http import HTTPStatus


class ServiceError(Exception):
    """Base class for errors that map to a clean HTTP response."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    code: str = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

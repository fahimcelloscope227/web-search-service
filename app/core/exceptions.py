from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class ServiceError(Exception):
    """Base class for errors that map to a clean HTTP response."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ProviderConfigurationError(ServiceError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "provider_misconfigured"


class SearchProviderError(ServiceError):
    status_code = status.HTTP_502_BAD_GATEWAY
    code = "search_provider_error"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ServiceError)
    async def _handle_service_error(_: Request, exc: ServiceError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

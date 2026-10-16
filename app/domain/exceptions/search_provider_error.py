from http import HTTPStatus

from app.domain.exceptions.service_error import ServiceError


class SearchProviderError(ServiceError):
    status_code = HTTPStatus.BAD_GATEWAY
    code = "search_provider_error"

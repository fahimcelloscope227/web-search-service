from http import HTTPStatus

from app.domain.exceptions.service_error import ServiceError


class ProviderConfigurationError(ServiceError):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    code = "provider_misconfigured"

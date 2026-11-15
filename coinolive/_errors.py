import builtins


class CoinoLiveError(Exception):
    """The parent of every error this library raises."""


class ApiError(CoinoLiveError):
    """The API refused the request; str(e) says why."""

    def __init__(self, message, status=0, errors=None):
        super().__init__(message)
        self.message = message
        self.status = status
        #: Field errors, when the API names fields: {"amount": ["…"]}.
        self.errors = errors or {}


class AuthenticationError(ApiError):
    """Missing, wrong or revoked API key, or the gateway is suspended (401)."""


class NotFoundError(ApiError):
    """Not found, or it belongs to another gateway (404)."""


class ValidationError(ApiError):
    """The request was refused; errors names the fields (422)."""


class RateLimitError(ApiError):
    """Too many requests (429). Retried automatically, then raised."""


class ConnectionError(CoinoLiveError, builtins.ConnectionError):
    """Coino Live could not be reached (network, DNS, timeout). Retried automatically, then raised."""


class SignatureVerificationError(CoinoLiveError):
    """A webhook whose signature is missing, wrong or too old: refuse it."""

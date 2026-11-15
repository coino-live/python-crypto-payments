"""Coino Live API v2 client for Python 3.8+ (standard library only).

    import coinolive

    coino = coinolive.Client("ck_live_…")
    payment = coino.payments.create(amount="25.00", currency="EUR", order_id="1001")
    return redirect(payment["checkout_url"])
"""

from ._client import DEFAULT_BASE_URL, VERSION, Client
from ._errors import (
    ApiError,
    AuthenticationError,
    CoinoLiveError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
    SignatureVerificationError,
    ValidationError,
)
from . import webhooks

__version__ = VERSION

__all__ = [
    "Client",
    "webhooks",
    "VERSION",
    "DEFAULT_BASE_URL",
    "CoinoLiveError",
    "ApiError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ConnectionError",
    "SignatureVerificationError",
]

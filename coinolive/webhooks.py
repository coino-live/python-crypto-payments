"""Webhook signatures: X-Coino-Signature: t=<unix time>,v1=<hex HMAC-SHA256(secret, "<t>.<raw body>")>.

    event = coinolive.webhooks.verify(request.body, request.headers.get("X-Coino-Signature"), secret)
    payment = coino.payments.retrieve(event["data"]["id"])  # Read the payment before acting on it.
"""

import hashlib
import hmac
import json
import time

from ._errors import SignatureVerificationError


def verify(payload, signature_header, secret, tolerance=300):
    """Returns the decoded event, or raises SignatureVerificationError.

    :param payload: the raw request body (bytes or str), not parsed JSON
    :param signature_header: the X-Coino-Signature header
    :param secret: the gateway's signing secret
    :param tolerance: seconds a signature stays valid
    """
    if isinstance(payload, (bytes, bytearray)):
        payload = bytes(payload).decode("utf-8")
    if not isinstance(payload, str):
        raise SignatureVerificationError("Pass the raw request body (bytes or str), not parsed JSON.")

    parts = {}
    for pair in (signature_header or "").split(","):
        key, sep, value = pair.strip().partition("=")
        if sep:
            parts[key] = value
    t, v1 = parts.get("t", ""), parts.get("v1", "")
    if not t or not v1 or not t.isdigit():
        raise SignatureVerificationError("The X-Coino-Signature header is missing or malformed.")
    if abs(time.time() - int(t)) > tolerance:
        raise SignatureVerificationError("The signature is too old.")
    expected = hmac.new(secret.encode("utf-8"), (t + "." + payload).encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, v1):
        raise SignatureVerificationError("The signature does not match.")
    try:
        event = json.loads(payload)
    except ValueError:
        event = None
    if not isinstance(event, dict):
        raise SignatureVerificationError("The payload is not JSON.")
    return event

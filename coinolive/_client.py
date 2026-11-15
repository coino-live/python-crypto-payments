import json
import platform
import re
import secrets
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

from ._errors import (
    ApiError,
    AuthenticationError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

VERSION = "1.0.0"
DEFAULT_BASE_URL = "https://coino.live/api/v2"


def _query(params):
    pairs = [(k, str(v)) for k, v in params.items() if v is not None and v != ""]
    return "?" + urllib.parse.urlencode(pairs) if pairs else ""


def _id(value):
    return urllib.parse.quote(str(value), safe="")


class Payments:
    """Payments: create one per order, send the customer to its checkout_url, read it back before shipping."""

    def __init__(self, client):
        self._client = client

    def create(self, params=None, *, idempotency_key=None, **fields):
        """Creates a payment: create(amount="25.00", currency="EUR", order_id="1001", success_url=…, notify_url=…),
        or create({"amount": "25.00", …}).

        Without an idempotency key a random one is used, so a retried request never creates a second payment.
        Pass your own key (for example "order-1001-1") to make repeating the call from your code safe too.
        """
        body = dict(params or {}, **fields)
        key = idempotency_key or secrets.token_hex(16)
        return self._client.request("POST", "/payments", body, idempotency_key=key)["data"]

    def retrieve(self, payment_id):
        return self._client.request("GET", "/payments/" + _id(payment_id))["data"]

    def list(self, status=None, order_id=None, cursor=None):
        """One page of payments (50), newest first: {"data": […], "meta": {"next_cursor": …, "prev_cursor": …}}."""
        return self._client.request("GET", "/payments" + _query({"status": status, "order_id": order_id, "cursor": cursor}))

    def all(self, status=None, order_id=None):
        """Every payment matching the filters, fetching pages as you go."""
        cursor = None
        while True:
            page = self.list(status=status, order_id=order_id, cursor=cursor)
            yield from page["data"]
            cursor = (page.get("meta") or {}).get("next_cursor")
            if not cursor:
                return

    def cancel(self, payment_id):
        """Cancels an open payment that has received nothing."""
        return self._client.request("POST", "/payments/" + _id(payment_id) + "/cancel", repeatable=True)["data"]


class Custody:
    """Custody users: lifetime deposit addresses and balances for the users of your app."""

    def __init__(self, client):
        self._client = client

    def create(self, external_id, **params):
        """Creates a user, or returns the existing one with the same external_id. Optional: name, email, metadata."""
        return self._client.request("POST", "/custody/users", dict(params, external_id=external_id), repeatable=True)["data"]

    def retrieve(self, user_id):
        return self._client.request("GET", "/custody/users/" + _id(user_id))["data"]

    def list(self, external_id=None, cursor=None):
        """One page of users (50), newest first: {"data": […], "meta": {"next_cursor": …, "prev_cursor": …}}."""
        return self._client.request("GET", "/custody/users" + _query({"external_id": external_id, "cursor": cursor}))

    def deposits(self, user_id, cursor=None):
        """One page of a user's credited deposits (50), newest first: {"data": […], "next_cursor": …}."""
        return self._client.request("GET", "/custody/users/" + _id(user_id) + "/deposits" + _query({"cursor": cursor}))

    def transfer(self, user_id, asset, amount=None):
        """Moves a user's balance of one asset to your main balance: all of it, or just amount."""
        body = {"asset": asset} if amount is None else {"asset": asset, "amount": str(amount)}
        return self._client.request("POST", "/custody/users/" + _id(user_id) + "/transfers", body)["data"]


class Withdrawals:
    """API withdrawals. Turn them on in the gateway settings first."""

    def __init__(self, client):
        self._client = client

    def create(self, asset, amount, address, reference=None, custody_user=None):
        """Sends coins from your balance (or a custody user's balance) to an address.

        Give a reference: the same reference returns the same withdrawal, so a retried request never pays twice.
        """
        body = {"asset": asset, "amount": str(amount), "address": address}
        if reference is not None:
            body["reference"] = reference
        if custody_user is not None:
            body["custody_user"] = custody_user
        return self._client.request("POST", "/withdrawals", body, repeatable=reference is not None)["data"]

    def retrieve(self, withdrawal_id):
        return self._client.request("GET", "/withdrawals/" + _id(withdrawal_id))["data"]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


_opener = urllib.request.build_opener(_NoRedirect())


class Client:
    """Coino Live API client.

    :param api_key: ck_live_… (Dashboard → Developers)
    :param base_url: https://coino.live/api/v2 unless you were given another
    :param timeout: seconds per request
    :param max_retries: retries for network errors, 429 and 5xx (only for requests that are safe to repeat)
    """

    def __init__(self, api_key, base_url=DEFAULT_BASE_URL, timeout=30, max_retries=2):
        if not isinstance(api_key, str) or not re.match(r"^ck_(live|test)_[A-Za-z0-9]+$", api_key):
            raise ValueError("An API key looks like ck_live_… (create one in your dashboard under Developers).")
        self._api_key = api_key
        self._base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        if not self._base_url.startswith("https://") and not re.match(r"^http://(localhost|127\.0\.0\.1)(:\d+)?(/|$)", self._base_url):
            raise ValueError("base_url must start with https://.")
        self._timeout = timeout
        self._max_retries = max(0, int(max_retries))

        self.payments = Payments(self)
        self.custody = Custody(self)
        self.withdrawals = Withdrawals(self)

    def currencies(self):
        """Currencies a payment can be priced in: [{"code": "EUR", "usd_per_unit": "1.09"}, …]."""
        return self.request("GET", "/currencies")["data"]

    def assets(self):
        """Coins customers can pay with right now."""
        return self.request("GET", "/assets")["data"]

    def balances(self):
        """Your account balance per coin, after fees."""
        return self.request("GET", "/balances")["data"]

    def request(self, method, path, body=None, idempotency_key=None, repeatable=False):
        """Internal: use the resources. Returns the decoded JSON answer."""
        # Retrying a POST is only safe when repeating it returns the same object (an idempotency key, a custody
        # external_id, a withdrawal reference).
        retriable = method == "GET" or bool(idempotency_key) or repeatable
        attempt = 0
        while True:
            try:
                return self._send(method, path, body, idempotency_key)
            except (ConnectionError, ApiError) as e:
                temporary = isinstance(e, (ConnectionError, RateLimitError)) or getattr(e, "status", 0) >= 500
                if not retriable or not temporary or attempt >= self._max_retries:
                    raise
                time.sleep(min(8, 0.5 * 2 ** attempt))
                attempt += 1

    def _send(self, method, path, body, idempotency_key):
        headers = {
            "Authorization": "Bearer " + self._api_key,
            "Accept": "application/json",
            "User-Agent": "coinolive-python/%s Python/%s" % (VERSION, platform.python_version()),
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(self._base_url + path, data=data, method=method, headers=headers)
        try:
            with _opener.open(req, timeout=self._timeout) as r:
                status, raw = r.status, r.read()
        except urllib.error.HTTPError as e:
            status, raw = e.code, e.read()
        except (urllib.error.URLError, socket.timeout, OSError) as e:
            raise ConnectionError("Could not reach Coino Live: %s" % getattr(e, "reason", e)) from e

        try:
            payload = json.loads(raw.decode("utf-8")) if raw else None
        except ValueError:
            payload = None
        is_object = isinstance(payload, dict)

        if 200 <= status < 300 and is_object:
            return payload
        if 300 <= status < 400 or (status == 404 and not is_object):
            raise ApiError("There is no Coino Live API at %s (HTTP %d). Check base_url." % (self._base_url, status), status)

        message = str(payload["message"]) if is_object and payload.get("message") else "HTTP %d" % status
        errors = payload["errors"] if is_object and isinstance(payload.get("errors"), dict) else {}
        cls = {401: AuthenticationError, 404: NotFoundError, 422: ValidationError, 429: RateLimitError}.get(status, ApiError)
        raise cls(message, status, errors)

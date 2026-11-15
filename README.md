# Coino Live Python library

> **Updating from the old version?** Earlier code in this repository used the Coino Live API v1, which has been retired: its endpoints (`/api/v1/...`) no longer answer. This version uses the current [API v2](https://coino.live/api-guide). Replace the old files with these.

Accept crypto payments with the [Coino Live API](https://coino.live/api-guide). Python 3.8+, standard library only.

## Install

Download `coinolive-python-<version>.zip` from [coino.live/api-guide](https://coino.live/api-guide#libraries), unzip it
and install the folder:

```bash
pip install ./coinolive-python
```

Or copy the `coinolive` folder inside it next to your code.

## Take a payment

```python
import coinolive

coino = coinolive.Client("ck_live_…")  # Dashboard → Developers

payment = coino.payments.create(
    amount="25.00",          # a string, at most 2 decimals
    currency="EUR",          # any code from coino.currencies(); USD by default
    order_id="1001",
    success_url="https://shop.example/thanks",
    cancel_url="https://shop.example/cart",
    notify_url="https://shop.example/coino-webhook",
)

return redirect(payment["checkout_url"])
```

Ship the order when a fresh read says `paid`:

```python
payment = coino.payments.retrieve(payment_id)
if payment["status"] == "paid":
    ...
```

Statuses: `open`, `confirming`, `partially_paid`, `paid`, `expired`, `cancelled`.

## Webhooks

The signature covers the raw body, so pass it unparsed:

```python
from coinolive import webhooks, SignatureVerificationError

@app.post("/coino-webhook")  # Flask
def coino_webhook():
    try:
        event = webhooks.verify(request.get_data(), request.headers.get("X-Coino-Signature"), SIGNING_SECRET)
    except SignatureVerificationError:
        return "", 401
    if event["event"].startswith("payment."):
        payment = coino.payments.retrieve(event["data"]["id"])  # act on what the API says, not on the webhook body
    return "", 200
```

In Django use `request.body` and `request.headers.get("X-Coino-Signature")`.

## Everything else

```python
coino.payments.list(status="paid", order_id="1001")   # {"data": […], "meta": {"next_cursor": …}}
for payment in coino.payments.all(status="paid"):     # every page
    ...
coino.payments.cancel(payment_id)                     # only while nothing was received

coino.currencies()                                    # prices can be in these
coino.assets()                                        # customers can pay with these
coino.balances()                                      # your balance per coin, with usd_value

user = coino.custody.create("user-42", name="Ada")    # lifetime deposit addresses for your users
coino.custody.retrieve(user["id"])
coino.custody.list(external_id="user-42")
coino.custody.deposits(user["id"])
coino.custody.transfer(user["id"], "usdt-tron")       # move the user's balance to yours

coino.withdrawals.create("usdt-tron", "50", "T…", reference="payout-77")
coino.withdrawals.retrieve(withdrawal_id)
```

## Errors and retries

Every failure raises one of these (all in `coinolive`):

| Error | When |
| --- | --- |
| `AuthenticationError` | Wrong or revoked key, or the gateway is suspended (401) |
| `NotFoundError` | Unknown ID, or it belongs to another gateway (404) |
| `ValidationError` | The request was refused; `e.errors` names the fields (422) |
| `RateLimitError` | Too many requests (429) |
| `ApiError` | Anything else; the parent of the four above, with `e.status` |
| `ConnectionError` | The API could not be reached, or the request timed out |

All of them inherit from `CoinoLiveError`.

Network errors, 429 and 5xx answers are retried twice with a short pause, but only for requests that are safe to repeat:
reads, `payments.create()` (it always sends an idempotency key, random unless you pass `idempotency_key=`),
`custody.create()` (same `external_id`, same user) and `withdrawals.create()` with a `reference`.

```python
coino = coinolive.Client("ck_live_…", timeout=30, max_retries=2, base_url="https://coino.live/api/v2")
```

## Tests

```bash
python tests/run.py
COINOLIVE_API_URL=https://… COINOLIVE_API_KEY=ck_test_… python tests/run.py   # also against a real API
```

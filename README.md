# Python Crypto Payments Library for the Coino Live API v2

Accept crypto payments in Python with the official library for the [Coino Live](https://coino.live) crypto payment gateway and its [REST API v2](https://coino.live/api-guide). With it you can create payment checkouts, verify webhooks, give your users lifetime deposit addresses, check balances and send withdrawals.

**Version:** 1.0.0 · **Requires:** Python 3.8+ · **Dependencies:** standard library only · **License:** MIT

> **Updating from the old version?** Earlier code in this repository used the Coino Live API v1, which has been retired: its endpoints (`/api/v1/...`) no longer answer. This version uses the current [API v2](https://coino.live/api-guide). Replace the old files with these.

## Supported assets, fees and payment flow

Coino Live is a crypto payment gateway that supports **117 assets on 11 networks**: Bitcoin, Litecoin, Ethereum, BNB Smart Chain, opBNB, Polygon, Base, Arbitrum, TRON, TON and Solana. USDT and USDC are available on most of these networks. Dogecoin and Bitcoin Cash are not accepted.

- **Platform fee:** 0.25% per payment. Blockchain network fees are separate.
- **Signup:** email and password, no KYC.
- **Payment flow:** payments are credited to your Coino Live balance, and you withdraw them to your own wallet.

## Install the Python library

Download `coinolive-python-<version>.zip` from [coino.live/api-guide](https://coino.live/api-guide#libraries), unzip it and install the folder:

```bash
pip install ./coinolive-python
```

Or copy the `coinolive` folder inside it next to your code.

## Create a crypto payment

Use your API key from **Dashboard → Developers**. Create a payment, then redirect your customer to its checkout URL from your web app's request handler:

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

### Confirm the payment before shipping the order

Ship the order only when a fresh read says `paid`:

```python
payment = coino.payments.retrieve(payment_id)
if payment["status"] == "paid":
    ...
```

Payment statuses: `open`, `confirming`, `partially_paid`, `paid`, `expired`, `cancelled`.

## Verify payment webhooks

The signature covers the raw request body, so pass the body to `verify()` unparsed:

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

In Django, use `request.body` and `request.headers.get("X-Coino-Signature")`.

## List and cancel payments

```python
coino.payments.list(status="paid", order_id="1001")   # {"data": […], "meta": {"next_cursor": …}}
for payment in coino.payments.all(status="paid"):     # every page
    ...
coino.payments.cancel(payment_id)                     # only while nothing was received
```

## Check currencies, assets and balances

```python
coino.currencies()                                    # prices can be in these
coino.assets()                                        # customers can pay with these
coino.balances()                                      # your balance per coin, with usd_value
```

## Give users lifetime deposit addresses

Create custody users with lifetime deposit addresses, list their deposits and move their balances to yours:

```python
user = coino.custody.create("user-42", name="Ada")    # lifetime deposit addresses for your users
coino.custody.retrieve(user["id"])
coino.custody.list(external_id="user-42")
coino.custody.deposits(user["id"])
coino.custody.transfer(user["id"], "usdt-tron")       # move the user's balance to yours
```

## Create and retrieve withdrawals

```python
coino.withdrawals.create("usdt-tron", "50", "T…", reference="payout-77")
coino.withdrawals.retrieve(withdrawal_id)
```

## Handle errors and retries

Every failure raises one of these exceptions, all available from `coinolive`:

| Error | When |
| --- | --- |
| `AuthenticationError` | Wrong or revoked key, or the gateway is suspended (401) |
| `NotFoundError` | Unknown ID, or it belongs to another gateway (404) |
| `ValidationError` | The request was refused; `e.errors` names the fields (422) |
| `RateLimitError` | Too many requests (429) |
| `ApiError` | Anything else; the parent of the four above, with `e.status` |
| `ConnectionError` | The API could not be reached, or the request timed out |

All of them inherit from `CoinoLiveError`.

Network errors, 429 responses and 5xx responses are retried twice with a short pause, but only for requests that are safe to repeat:

- reads
- `payments.create()`, which always sends an idempotency key (random unless you pass `idempotency_key=`)
- `custody.create()`, where the same `external_id` means the same user
- `withdrawals.create()` with a `reference`

You can set the timeout, retries and base URL on the client:

```python
coino = coinolive.Client("ck_live_…", timeout=30, max_retries=2, base_url="https://coino.live/api/v2")
```

## Run the tests

```bash
python tests/run.py
COINOLIVE_API_URL=https://… COINOLIVE_API_KEY=ck_test_… python tests/run.py   # also against a real API
```

## Documentation and license

Full API reference: [coino.live/api-guide](https://coino.live/api-guide). This library is released under the MIT License.

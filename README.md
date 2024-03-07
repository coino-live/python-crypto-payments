# CoinoLive Python Client

## Introduction

CoinoLive Python Client is a Python wrapper for interacting with the CoinoLive API. It provides a convenient way to integrate CoinoLive's crypto payment gateway functionality into Python applications.

## Why Choose Us?

- **No KYC:** You can sign up and start accepting payments in minutes, with just an email address and a password.
- **Sky's the Limit:** You can access your money anytime, anywhere, and in any currency you prefer.
- **Affordable and Fair:** We charge only a flat fee of 0.25% per transaction.
- **Safe and Sound:** We use the latest encryption and security protocols to protect your data and funds.
- **Seamless and Simple:** We provide a user-friendly interface. You can also customize your payment page and checkout process to suit your brand and preferences.

## Installation

To install CoinoLive Python Client, simply clone this repository:

```bash
git clone https://github.com/coino-live/python-crypto-payments.git
```

## Usage

1. Import the `CoinoLive` class into your Python project:

    ```python
    from coino_live import CoinoLive
    ```

2. Initialize a `CoinoLive` object with your API key:

    ```python
    api_key = "YOUR_API_KEY_HERE"
    coino_live = CoinoLive(api_key)
    ```

3. Use the provided methods to interact with the CoinoLive API. For example:

    ```python
    # Create Order
    order_response = coino_live.create_order(amount=10, callback_url="https://domain.com/verify_payment",
                                              description="Pay For shoes", gate_id="M-2")
    order_id = order_response["Order_ID"]

    # Redirect Payment
    coino_live.redirect_payment(order_id)

    # Verify Payment
    verification_response = coino_live.verify_payment(order_id)
    ```


## Documentation

For detailed information on how to install, configure, and use the Coino Live WooCommerce Plugin, please refer to our [Documentation](https://coino.live/document).

## Support

For any questions, issues, or feedback related to the Coino Live WooCommerce Plugin, please reach out to our support team at [support@coino.live](mailto:support@coino.live).

## Contributing

We welcome contributions from the community to improve the Coino Live WooCommerce Plugin. If you have any suggestions, bug fixes, or feature requests, please open an issue or submit a pull request.

## Connect with Us

Stay updated with the latest news and updates from Coino Live:

- Follow us on [Twitter](https://twitter.com/coino_live)
- Follow us on [Instagran](https://www.instagram.com/coino.live)
- Follow us on [Linkedin](https://linkedin.com/company/coino-live)
- Subscribe to our [Blog](https://coino.live/blog)
  
## Products

- [Accept Crypto Payments](https://coino.live/crypto-gateway)
- [Personal Crypto Gateway](https://coino.live/personal-crypto-gateway)
- [Crypto Donation](https://coino.live/crypto-donation)
- [Invoice Manager](https://coino.live/invoice-manager)
- [POS Crypto Payment Terminal](https://coino.live/point-of-sale)
- [Crypto Form Builder](https://coino.live/form-builder)

## Links

- [Website](https://coino.live)
- [About Us](https://coino.live/about)
- [Contact Us](https://coino.live/contact)
- [FAQ](https://coino.live/faq)


Thank you for choosing Coino Live for your cryptocurrency payment gateway needs!

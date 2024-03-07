import requests

class CoinoLive:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://coino.live/api/v1/"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }

    def create_order(self, amount, callback_url, description, gate_id):
        payload = {
            "Amount": amount,
            "Callback": callback_url,
            "Description": description,
            "Gate_ID": gate_id,
            "Create": True
        }
        response = requests.post(self.base_url + "order", json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def redirect_payment(self, order_id):
        payment_url = f"https://coino.live/orders/{order_id}"
        print("Redirecting to payment URL:", payment_url)

    def verify_payment(self, order_id):
        response = requests.get(self.base_url + f"verify?order={order_id}", headers=self.headers)
        response.raise_for_status()
        return response.json()

# Example usage:
if __name__ == "__main__":
    api_key = "YOUR_API_KEY_HERE"
    coino_live = CoinoLive(api_key)

    # Create Order
    order_response = coino_live.create_order(amount=10, callback_url="https://domain.com/verify_payment",
                                              description="Pay For shoes", gate_id="M-2")
    order_id = order_response["Order_ID"]
    print("Order created. ID:", order_id)

    # Redirect Payment
    coino_live.redirect_payment(order_id)

    # Verify Payment
    verification_response = coino_live.verify_payment(order_id)
    print("Payment verification:", verification_response)

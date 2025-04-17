import requests
import uuid
from django.conf import settings
from rest_framework.response import Response

def initiate_payment(amount, email, order_id):
    """Initiate a payment request to Flutterwave."""
    url = "https://api.flutterwave.com/v3/payments"
    headers = {
        "Authorization": f"Bearer {settings.FLW_SEC_KEY}",  # Make sure FLW_SEC_KEY is in settings
        "Content-Type": "application/json"
    }

    data = {
        "tx_ref": str(uuid.uuid4()),  # Unique transaction reference
        "amount": str(amount),
        "currency": "NGN",
        "redirect_url": "http://127.0.0.1:8000/confirm/",  # Placeholder redirect URL
        "customer": {
            "email": email,
            "phonenumber": "080****4528",  # Placeholder phone
            "name": "Customer"  # Placeholder name
        },
        "customizations": {
            "title": "MB Shawarma Bite Payments",
            "logo": "https://example.com/logo.png"
        },
        "meta": {
            "order_id": order_id  # Store order ID for later verification
        },
        "payment_options": "card, ussd, banktransfer"
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()

        if response.status_code == 200 and response_data.get("status") == "success":
            payment_link = response_data["data"].get("link")
            return {"status": "success", "message": "Payment initiated", "data": {"link": payment_link}}

        return {"error": "Payment request failed", "details": response_data}

    except requests.exceptions.RequestException as err:
        return {"error": "Network request failed", "details": str(err)}

import requests
import uuid
from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def initiate_payment(request, order_id):
    """ Initiates Flutterwave payment """
    
    amount = 1000  # Replace with actual order amount
    email = request.user.email
    redirect_url = request.data.get("redirect_url", "http://127.0.0.1:5500/confirm.html")

    url = "https://api.flutterwave.com/v3/payments"
    headers = {
        "Authorization": f"Bearer {settings.FLW_SEC_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "tx_ref": str(uuid.uuid4()),
        "amount": str(amount),
        "currency": "NGN",
        "redirect_url": redirect_url,
        "customer": {
            "email": email,
            "phonenumber": "08012345678",
            "name": request.user.get_full_name()
        },
        "customizations": {
            "title": "My Store Payments",
            "logo": "https://example.com/logo.png"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()

        if response.status_code == 200 and response_data.get("status") == "success":
            return Response({"status": "success", "link": response_data["data"]["link"]})

        return Response({"error": "Payment link not received", "details": response_data}, status=400)

    except requests.exceptions.RequestException as err:
        return Response({"error": "Payment request failed", "details": str(err)}, status=500)

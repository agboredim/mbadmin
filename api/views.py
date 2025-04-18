from itertools import product
from urllib import response
from django.shortcuts import render, get_object_or_404
from api.filters import ProductFilter
from rest_framework.decorators import api_view, action
from .serializers import *
from storeapp.models import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.viewsets import ModelViewSet, GenericViewSet, ViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from api import serializers
from rest_framework import viewsets
from api.flutterwave import initiate_payment
import requests
from api.serializers import OrderSerializer, CreateOrderSerializer, UpdateOrderSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View 
import logging
import json
import hmac
import hashlib
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from geopy.distance import geodesic
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import authenticate,login,logout
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

SHOP_LOCATION = (6.60247, 3.30721)

logger = logging.getLogger(__name__)
User = get_user_model()


def initiate_payment(amount, email, order_id, delivery_price=0):
    total_amount = amount + delivery_price 
    url = "https://api.flutterwave.com/v3/payments"
    
    headers = {
        "Authorization": f"Bearer {settings.FLW_SEC_KEY}"
    }
    
    data = {
        "tx_ref": str(uuid.uuid4()),
        "amount": str(total_amount),
        "currency": "NGN",
        "redirect_url": f"http://127.0.0.1:5501/index.html{order_id}",
        "meta": {
            "consumer_id": 23,
            "consumer_mac": "92a3-912ba-1192a"
        },
        "customer": {
            "email": email,
            "phonenumber": "080****4528",
            "name": "Yemi Desola"
        },
        "customizations": {
            "title": "Pied Piper Payments",
            "logo": "http://www.piedpiper.com/app/themes/joystick-v27/images/logo.png"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        return Response(response_data)
    
    except requests.exceptions.RequestException as err:
        print("The payment didn't go through")
        return Response({"error": str(err)}, status=500)

class ProductsViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['old_price']
    pagination_class = PageNumberPagination


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs["product_pk"])

    def get_serializer_context(self):
        return {"product_id": self.kwargs["product_pk"]}


class CartViewSet(CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer


class CartItemViewSet(ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        return Cartitems.objects.filter(cart_id=self.kwargs["cart_pk"])

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        return {"cart_id": self.kwargs["cart_pk"]}



class OrderViewSet(ModelViewSet):
    http_method_names = ["get", "patch", "post", "delete", "options", "head"]

    def create(self, request, *args, **kwargs):
        """Creates an order and includes delivery price in total."""
        serializer = CreateOrderSerializer(data=request.data, context={"user_id": self.request.user.id})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        total_price = order.total_price

        serializer = OrderSerializer(order)
        return Response({
            "message": "Order created successfully",
            "subtotal": order.subtotal,
            "delivery_price": order.delivery_price,
            "total_price": total_price,
            "order": serializer.data
        })

    @action(detail=True, methods=['POST'])
    def pay(self, request, pk):
        """Initiates payment with total price (including delivery)."""
        order = self.get_object()
        amount = order.total_price 
        email = request.user.email
        order_id = str(order.id)
        return initiate_payment(amount, email, order_id)

    @action(detail=False, methods=["POST"])
    def confirm_payment(self, request):
        """Handles payment confirmation."""
        order_id = request.GET.get("o_id")
        order = Order.objects.get(id=order_id)
        order.pending_status = "C"
        order.save()
        serializer = OrderSerializer(order)
        
        return Response({
            "msg": "Payment was successful",
            "data": serializer.data
        })

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        elif self.request.method == 'PATCH':
            return UpdateOrderSerializer
        return OrderSerializer

    def get_queryset(self):
        """Filters orders based on user type."""
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(owner=user)


class ProfileViewSet(ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        name = request.data["name"]
        bio = request.data["bio"]
        picture = request.data["picture"]

        Profile.objects.create(name=name, bio=bio, picture=picture)

        return Response("Profile created successfully", status=status.HTTP_200_OK)

def index(request):
    return render(request, 'index.html',)

def address_detail(request):
    return render(request, 'address.html',)


def order_list(request):
    search_query = request.GET.get('search', '')

    if search_query:
        orders = Order.objects.filter(transaction_ref__icontains=search_query)
    else:
        orders = Order.objects.all()

    return render(request, 'order.html', {'orders': orders})


def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    address = order.address if hasattr(order, 'address') else None
    

    return render(request, 'order_detail.html', {'order': order, 'address': address})


class ProductViewSet(ViewSet):
    """
    A ViewSet to group products by categories.
    """

    @action(detail=False, methods=['get'], url_path='grouped-by-category')
    def grouped_by_category(self, request):
        categories = Category.objects.all()
        response_data = {}

        for category in categories:
            products = Product.objects.filter(category=category)
            serializer = ProductSerializer(products, many=True)
            response_data[category.name] = serializer.data

        return Response(response_data)


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    
class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "Password reset link sent to email"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class PasswordResetConfirmView(APIView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# def loginpage(request):
#     if request.method == "POST":
#         form = AuthenticationForm(request, data=request.POST)
#         if form.is_valid():
#             user = form.get_user()
#             login(request, user)
#             messages.success(request, "Login successful!")
#             return redirect("index")
#         else:
#             messages.error(request, "Invalid username or password.")
#     else:
#         form = AuthenticationForm()

#     return render(request, "loginpage.html", {"form": form})

def logoutpage(request):
    logout(request)
    return redirect('index')
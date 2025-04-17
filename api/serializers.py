from importlib.resources import read_binary
from itertools import product
from django.db import transaction
from rest_framework import serializers
from  storeapp.models import *
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
import logging


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["category_id", "title", "slug", "products"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [ "id", "name", "description","image", "category", "slug", "inventory", "price"]
    
    category = CategorySerializer()

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "date_created", "name", "description"]
    
    def create(self, validated_data):
        product_id = self.context["product_id"]
        return Review.objects.create(product_id = product_id,  **validated_data)


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id","name", "price"]
        
        
        

class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(many=False)
    sub_total = serializers.SerializerMethodField( method_name="total")
    class Meta:
        model= Cartitems
        fields = ["id", "cart", "product", "quantity", "sub_total"]
        
    
    def total(self, cartitem:Cartitems):
        return cartitem.quantity * cartitem.product.price
    

class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField()
    
    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError("There is no product associated with the given ID")
        
        return value
    
    def save(self, **kwargs):
        cart_id = self.context["cart_id"]
        product_id = self.validated_data["product_id"] 
        quantity = self.validated_data["quantity"] 
        
        try:
            cartitem = Cartitems.objects.get(product_id=product_id, cart_id=cart_id)
            cartitem.quantity += quantity
            cartitem.save()
            
            self.instance = cartitem
            
        
        except:
            
            self.instance = Cartitems.objects.create(cart_id=cart_id, **self.validated_data)
            
        return self.instance
         

    class Meta:
        model = Cartitems
        fields = ["id", "product_id", "quantity"]





class UpdateCartItemSerializer(serializers.ModelSerializer):
    # id = serializers.IntegerField(read_only=True)
    class Meta:
        model = Cartitems
        fields = ["quantity"]


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    grand_total = serializers.SerializerMethodField(method_name='main_total')
    
    class Meta:
        model = Cart
        fields = ["id", "items", "grand_total"]
        
    
    
    def main_total(self, cart: Cart):
        items = cart.items.all()
        total = sum([item.quantity * item.product.price for item in items])
        return total


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    class Meta:
        model = OrderItem 
        fields = ["id", "product", "quantity"]
        


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    subtotal = serializers.ReadOnlyField()
    delivery_price = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Order 
        fields = ['id', "placed_at", "pending_status", "owner", "items", "subtotal", "delivery_price", "total_price"]
 



class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()
    
    
    
    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError("This cart_id is invalid")
        
        elif not Cartitems.objects.filter(cart_id=cart_id).exists():
            raise serializers.ValidationError("Sorry your cart is empty")
        
        return cart_id
    
    
    
    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data["cart_id"]
            user_id = self.context["user_id"]
            order = Order.objects.create(owner_id = user_id)
            cartitems = Cartitems.objects.filter(cart_id=cart_id)
            orderitems = [
                OrderItem(order=order, 
                    product=item.product, 
                    quantity=item.quantity
                    )
            for item in cartitems
            ]
            OrderItem.objects.bulk_create(orderitems)
            # Cart.objects.filter(id=cart_id).delete()
            return order


class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order 
        fields = ["pending_status"]

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["id", "name", 'bio', "picture"]
        
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id", "phone_number", "street_address", "directions", "state", "city", "country", "postal_code"]
        extra_kwargs = {"user": {"required": False}}


User = get_user_model()
logger = logging.getLogger(__name__)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        reset_link = f"http://127.0.0.1:5500/password_reset.html?uid={uid}&token={token}"
        logger.info(f"Generated password reset link: {reset_link}")

        try:
            send_mail(
                "Password Reset Request",
                f"Click the link to reset your password: {reset_link}",
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise serializers.ValidationError("Failed to send password reset email.")

        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(min_length=6, write_only=True)

    def validate(self, data):
        try:
            uid = urlsafe_base64_decode(data["uid"]).decode()
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            raise serializers.ValidationError({"uid": "Invalid or expired UID"})

        if not default_token_generator.check_token(user, data["token"]):
            raise serializers.ValidationError({"token": "Invalid or expired token"})

        data["user"] = user
        return data

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["password"])
        user.save()
        return user
    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid token or user"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate token
        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate new password
        new_password = request.data.get("password")
        if not new_password or len(new_password) < 6:
            return Response({"error": "Password must be at least 6 characters long"}, status=status.HTTP_400_BAD_REQUEST)

        # Set new password
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password successfully reset"}, status=status.HTTP_200_OK)
    new_password = serializers.CharField(write_only=True)
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            uid = urlsafe_base64_decode(data["uid"]).decode()
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError):
            raise serializers.ValidationError("Invalid reset link.")

        if not default_token_generator.check_token(user, data["token"]):
            raise serializers.ValidationError("Invalid or expired token.")

        user.set_password(data["new_password"])
        user.save()

        return {"message": "Password reset successful."}
from django.db import models
import uuid
from django.conf import settings
from django.core.validators import RegexValidator
from geopy.distance import geodesic
from django.contrib.auth.models import User
from django import forms

SHOP_LOCATION = (6.5925, 3.3215)

        
class Category(models.Model):
    title = models.CharField(max_length=200)
    category_id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, unique=True)
    slug = models.SlugField(default= None)
    featured_product = models.OneToOneField('Product', on_delete=models.CASCADE, blank=True, null=True, related_name='featured_product')
    icon = models.CharField(max_length=100, default=None, blank = True, null=True)

    def __str__(self):
        return self.title



class Review(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name = "reviews")
    date_created = models.DateTimeField(auto_now_add=True)
    description = models.TextField(default="description")
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.description

    

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    discount = models. BooleanField(default=False)
    image = models.ImageField(upload_to = 'img',  blank = True, null=True, default='')
    price = models.FloatField(default=100.00)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True, related_name='products')
    slug = models.SlugField(default=None)
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, unique=True)
    inventory = models.IntegerField(default=5)
    top_deal=models.BooleanField(default=False)
    flash_sales = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name


class Cart(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return str(self.id)

class Cartitems(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items", null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True, related_name='cartitems')
    quantity = models.PositiveSmallIntegerField(default=0)
    

class Order(models.Model):
    PAYMENT_STATUS_PENDING = 'P'
    PAYMENT_STATUS_COMPLETE = 'C'
    PAYMENT_STATUS_FAILED = 'F'

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, 'Pending'),
        (PAYMENT_STATUS_COMPLETE, 'Complete'),
        (PAYMENT_STATUS_FAILED, 'Failed'),
    ]

    placed_at = models.DateTimeField(auto_now_add=True)
    pending_status = models.CharField(
        max_length=1, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_PENDING
    )
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    text = models.TextField(blank=True, null=True)
    transaction_ref = models.CharField(max_length=100, unique=True, null=True, blank=True)
    address = models.ForeignKey('Address', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Order #{self.id} - {self.owner.username} - {self.pending_status}"

    @property
    def subtotal(self):
        """Calculates total price of items without delivery."""
        items = self.items.all()
        return sum([item.quantity * item.product.price for item in items])

    @property
    def delivery_price(self):
        """Calculates delivery cost based on distance."""
        if not self.address:
            return 0  # No delivery charge if no address is provided

        user_location = (self.address.latitude, self.address.longitude)
        distance_km = geodesic(SHOP_LOCATION, user_location).km

        # Delivery pricing logic (similar to Chowdeck)
        if distance_km <= 2:
            return 500
        elif distance_km <= 5:
            return 1000
        elif distance_km <= 10:
            return 1500
        elif distance_km <= 15:
            return 2000
        else:
            return 2500  # Maximum cap

    @property
    def total_price(self):
        """Final total including delivery."""
        return self.subtotal + self.delivery_price

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.product.name
 
class Profile(models.Model):
    name = models.CharField(max_length=30)
    bio = models.TextField()
    picture = models.ImageField(upload_to = 'img', blank=True, null=True)
    
    def __str__(self):
        return self.name
  
 

class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='addresses'
    )
    city = models.CharField(max_length=255, db_index=True)
    country = models.CharField(max_length=255, db_index=True)
    directions = models.TextField(null=True, blank=True)
    street_address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')],
        null=True,
        blank=True
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def calculate_distance(self):
        """Returns distance from shop to user address in km"""
        if self.latitude and self.longitude:
            user_location = (self.latitude, self.longitude)
            return geodesic(SHOP_LOCATION, user_location).km
        return None

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.country}"
    
    
class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
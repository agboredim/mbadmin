from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView


router = DefaultRouter()

# Main resources
router.register("products", views.ProductsViewSet)
router.register("categories", views.CategoryViewSet)
router.register("carts", views.CartViewSet)
router.register("n_profiles", views.ProfileViewSet)
router.register("orders", views.OrderViewSet, basename="orders")
router.register("addresses", views.AddressViewSet, basename="addresses")
# router.register('webhook/flutterwave', PaymentWebhookViewSet, basename='webhook-flutterwave')


product_router = routers.NestedDefaultRouter(router, "products", lookup="product")
product_router.register("reviews", views.ReviewViewSet, basename="product-reviews")


cart_router = routers.NestedDefaultRouter(router, "carts", lookup="cart")
cart_router.register("items", views.CartItemViewSet, basename="cart-items")


# URL Patterns
urlpatterns = [
    path("", include(router.urls)),
    path("", include(product_router.urls)),
    path("", include(cart_router.urls)),
    path("auth/jwt/create", TokenObtainPairView.as_view(), name="jwt-create"),
]

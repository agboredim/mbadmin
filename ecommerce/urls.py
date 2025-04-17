"""
ecommerce URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from api import views
from django.conf.urls.static import static
from django.conf import settings
from api.views import *
from api.views import PasswordResetRequestView, PasswordResetConfirmView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include("api.urls"), name="api"),
    path("auth/", include('djoser.urls')),
    path("auth/", include('djoser.urls.jwt')),

    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    path('index/', views.index, name="index"),
    path('order/', order_list, name='order_list'),
    path('order/<int:order_id>/', order_detail_view, name='order_detail'),
    path('address/', address_detail, name='address_detail'),
    path("", loginpage, name="loginpage"),
    path('logoutpage/', views.logoutpage, name='logoutpage')
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

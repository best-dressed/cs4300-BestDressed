"""
URL configuration for users app.

"""

from django.urls import path
from .views import *

urlpatterns = [
    path("auth/ebay_market_delete/", ebay_marketplace_deletion_notification, name="ebay_market_delete")
]

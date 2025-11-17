"""
URL configuration for users app.

"""

from django.urls import path
from .views import *

urlpatterns = [
    path("auth/ebay_market_delete/", ebay_marketplace_deletion_notification, name="ebay_market_delete"),
    path("ebay_add_items/", ebay_get_items, name="ebay_get_items"),
    path("ajax/add_item/", ajax_add_item, name="ajax_add_item"),
]

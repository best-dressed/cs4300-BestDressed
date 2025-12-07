"""Setup for each model to be added via admin portal"""
from django.contrib import admin
from .models import Item, UserProfile, WardrobeItem, Outfit
# Register your models here.
admin.site.register(Item)
admin.site.register(UserProfile)
admin.site.register(WardrobeItem)
admin.site.register(Outfit)

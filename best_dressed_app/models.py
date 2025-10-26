from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


# article of clothing item in the catalog
class Item(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=2000)
    image_url = models.URLField(max_length=2000, default="https://pangaia.com/cdn/shop/files/DNA_Oversized_T-Shirt_-Summit_Blue-1.png?crop=center&height=1999&v=1755260238&width=1500")
 
    # set up url for viewing a particular item
    def get_absolute_url(self):
        return reverse("item_detail", kwargs={'pk': self.pk})

# user profile to extend Django's 'User' model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    style_preferences = models.CharField(max_length=200, blank=True, help_text="e.g., casual, formal, streetwear")
    favorite_colors = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
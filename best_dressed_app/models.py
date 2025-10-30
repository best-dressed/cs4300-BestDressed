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

    def __str__(self):
        return self.title


# user profile to extend Django's 'User' model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    style_preferences = models.CharField(max_length=200, blank=True, help_text="e.g., casual, formal, streetwear")
    favorite_colors = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# items saved by a user to their wardrobe
class WardrobeItem(models.Model):
    """
    Represents an item in a user's personal wardrobe.
    
    Users can save items from the catalog or add their own.
    Each wardrobe item belongs to one user and can optionally
    reference a catalog item if it was saved from there.
    """
    
    # category choices - predefined options for organizing items
    CATEGORY_CHOICES = [
        ('top', 'Top'),
        ('bottom', 'Bottom'),
        ('dress', 'Dress'),
        ('outerwear', 'Outerwear'),
        ('shoes', 'Shoes'),
        ('accessory', 'Accessory'),
        ('other', 'Other'),
    ]
    
    # Foreign Key: links this wardrobe item to a specific user
    # on_delete=models.CASCADE means: if user is deleted, delete their wardrobe items too
    # related_name='wardrobe_items' lets us access items via user.wardrobe_items.all()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wardrobe_items')
    
    # basic item information
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True)
    
    # category with predefined choices (dropdown in forms)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    
    # image URL for the item
    image_url = models.URLField(max_length=2000, blank=True)
    
    # optional link to the original catalog item (if saved from catalog)
    # on_delete=models.SET_NULL means: if catalog item is deleted, keep wardrobe item but remove the link
    # null=True, blank=True makes this field optional
    catalog_item = models.ForeignKey(
        Item, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='saved_by_users'
    )
    
    # additional optional fields for organization
    color = models.CharField(max_length=100, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    season = models.CharField(max_length=50, blank=True, help_text="e.g., summer, winter, all-season")
    
    # automatic timestamps
    # auto_now_add=True sets the time when object is first created (never changes)
    # auto_now=True updates the time every time the object is saved
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # default ordering: newest items first
        ordering = ['-created_at']
        
        # prevent duplicate saves: user can't save the same catalog item twice
        # this creates a database constraint
        unique_together = [['user', 'catalog_item']]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
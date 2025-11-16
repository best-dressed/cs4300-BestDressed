from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


# article of clothing item in the catalog
class Item(models.Model):

    ITEM_TAG_CHOICES = {
        "Accessory": "accessory",
        "Torso": "torso",
        "Head": "head",
        "Legs": "legs",
        "Shoes": "shoes"
    }

    title = models.CharField(max_length=200)
    description = models.CharField(max_length=2000)

    # for main item listing so everything is more clean with user-added data
    short_description = models.CharField(max_length=75, default="")
    # 5000 is kind of insane but for some reason a lot of google image urls are >2000 length so goin with it
    image_url = models.URLField(max_length=5000, default="")
    tag = models.CharField(max_length=20, choices=ITEM_TAG_CHOICES, default="")

    # ebay ID For market delete and duplicate checking
    item_id = models.CharField(max_length=200, unique=True, null=True, blank=True)
    # blank = true allows these to be blank in forms, as we support non ebay items too.
    item_ebay_url = models.URLField(blank=True, null=True)
    seller_id = models.CharField(max_length=200, null=True, blank=True)

    # make it so short description created automatically from description
    def save(self, *args, **kwargs):
        if self.description:
            # if description is long, add ...
            if len(self.description) > 75:
                self.short_description = (self.description[:72] + "...")

            # otherwise just make it the same bc doesn't matter.
            else:
                self.short_description = self.description[:75]

        # if user put nothing, put nothing
        else:
            self.short_description = ""
        super().save(*args, **kwargs)

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


class Outfit(models.Model):
    """
    Represents a collection of wardrobe items.
    
    Users can create outfits by combining multiple items from their wardrobe.
    Each outfit belongs to one user and can contain multiple wardrobe items.
    """
    
    # Foreign Key: links this outfit to a specific user
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outfits')
    
    # Basic outfit information
    name = models.CharField(max_length=200, help_text="e.g., 'Summer Date Night', 'Office Monday'")
    description = models.TextField(max_length=1000, blank=True, help_text="Describe the outfit and when to wear it")
    
    # ManyToMany relationship: one outfit can have many items, one item can be in many outfits
    # This creates a separate "junction table" in the database to track the relationships
    items = models.ManyToManyField(
        WardrobeItem,
        related_name='outfits',
        blank=True,
        help_text="Items included in this outfit"
    )
    
    # Optional fields for organization
    occasion = models.CharField(
        max_length=50, 
        blank=True,
        choices=[
            ('casual', 'Casual'),
            ('business', 'Business/Professional'),
            ('formal', 'Formal'),
            ('athletic', 'Athletic/Workout'),
            ('night_out', 'Night Out'),
            ('date', 'Date'),
            ('other', 'Other'),
        ],
        help_text="What type of occasion is this outfit for?"
    )
    
    season = models.CharField(
        max_length=50, 
        blank=True,
        choices=[
            ('spring', 'Spring'),
            ('summer', 'Summer'),
            ('fall', 'Fall'),
            ('winter', 'Winter'),
            ('all', 'All Seasons'),
        ],
        help_text="What season is this outfit best for?"
    )
    
    # Track if this is a favorite outfit
    is_favorite = models.BooleanField(default=False, help_text="Mark as a favorite outfit")
    
    # Automatic timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Default ordering: favorites first, then newest
        ordering = ['-is_favorite', '-created_at']
        
        # Ensure outfit names are unique per user (can't have two outfits with same name)
        unique_together = [['user', 'name']]
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def item_count(self):
        """Helper method to get the number of items in this outfit"""
        return self.items.count()
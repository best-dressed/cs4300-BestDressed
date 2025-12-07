"""
Core data models for the best dressed app.

This module defines the main database models for managing users,
catalog items, personal wardrobes, outfits, and AI-generated recommendations.

Key models:
- Item: Represents a catalog item of clothing or accessory, including metadata such as title, description, image URL, tag, and optional eBay data.
- UserProfile: Extends the Django User model to store additional information such as bio, style preferences, and favorite colors.
- WardrobeItem: Represents items saved by a user in their personal wardrobe, optionally linked to a catalog item.
- Outfit: A collection of WardrobeItems that a user can assemble for specific occasions or seasons.
- SavedRecommendation: Stores AI-generated fashion recommendations and links to recommended catalog items.
- HiddenItem: Tracks items that a user chooses to hide from their view in item listings.

Each model includes helpful methods for display, URLs, and automatic timestamping.
"""
from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model() # pylint prefers this over import User for some reason so ig we're doin it


# article of clothing item in the catalog
class Item(models.Model):
    """
    Represents an article of clothing or accessory in the catalog.
    """
    ITEM_TAG_CHOICES = [
        ('top', 'Top'),
        ('bottom', 'Bottom'),
        ('dress', 'Dress'),
        ('outerwear', 'Outerwear'),
        ('shoes', 'Shoes'),
        ('accessory', 'Accessory'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    description = models.CharField(max_length=2000)

    # for main item listing so everything is more clean with user-added data
    short_description = models.CharField(max_length=75, default="")
    # 5000 is kind of insane but for some reason a lot of google image urls are >2000 length so goin with it
    image_url = models.URLField(max_length=5000, default="")

    tag = models.CharField(max_length=20, choices=ITEM_TAG_CHOICES, default="other")

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
                self.short_description = self.description[:72] + "..."

            # otherwise just make it the same bc doesn't matter.
            else:
                self.short_description = self.description[:75]

        # if user put nothing, put nothing
        else:
            self.short_description = ""
        super().save(*args, **kwargs)

    # set up url for viewing a particular item
    def get_absolute_url(self):
        """Really basic method to get the url for an item"""
        return reverse("item_detail", kwargs={'pk': self.pk})

    def __str__(self):
        return self.title


# user profile to extend Django's 'User' model
class UserProfile(models.Model):
    """
    Extends the built-in Django User model with additional profile information.

    Fields:
    - user: One-to-one link to the Django User instance.
    - bio: Short biography or description of the user.
    - style_preferences: User's preferred fashion styles (e.g., casual, formal, streetwear).
    - favorite_colors: User's favorite colors.
    - created_at: Timestamp when the profile was created.
    - updated_at: Timestamp when the profile was last updated.
    """
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


class SavedRecommendation(models.Model):
    """
    Represents a saved AI recommendation for a user.

    Users receive AI-generated fashion recommendations based on their prompts.
    This model stores the history of these recommendations for later reference.
    """

    # Foreign Key: links this recommendation to a specific user
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_recommendations')

    # The user's prompt/request that generated this recommendation
    prompt = models.TextField(max_length=1000, help_text="User's request for recommendations")

    # The AI-generated recommendation text
    ai_response = models.TextField(help_text="AI-generated fashion recommendations")

    # ManyToMany relationship: track which catalog items were recommended
    recommended_items = models.ManyToManyField(
        Item,
        related_name='recommendations',
        blank=True,
        help_text="Catalog items that were recommended to the user"
    )

    # Automatic timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Default ordering: newest recommendations first
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.prompt[:50]}... ({self.created_at.strftime('%Y-%m-%d')})"

    def item_count(self):
        """Helper method to get the number of recommended items"""
        return self.recommended_items.count()

# For hiding items from user's particular view in item listing
class HiddenItem(models.Model):
    """
    Represents a catalog item that a user has chosen to hide.

    Each record links a specific user to a specific catalog item,
    preventing that item from appearing in the user's personal view
    of the item listings.

    Database constraints:
    - unique_together ensures a user cannot hide the same item multiple times.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="hidden_items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="hidden_by_users")

    class Meta:
        unique_together = [["user", "item"]]  # prevent duplicates

    def __str__(self):
        return f"{self.user.username} hid {self.item.title}"

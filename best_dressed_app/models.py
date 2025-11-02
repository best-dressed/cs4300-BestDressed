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
    image_url = models.URLField(max_length=2000, default="")
    tag = models.CharField(max_length=20, choices=ITEM_TAG_CHOICES, default="")

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
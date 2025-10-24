from django.db import models
from django.urls import reverse

# Create your models here.

# article of clothing item
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


from django.db import models
from django.urls import reverse

# Create your models here.

# article of clothing item
class Item(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=2000)
    image_url = models.URLField(max_length=2000, default="https://pangaia.com/cdn/shop/files/DNA_Oversized_T-Shirt_-Summit_Blue-1.png?crop=center&height=1999&v=1755260238&width=1500")
    # idk how this works yet but this is probably what we need for images, or a url
    # image = models.ImageField(upload_to='')

    # set up url for viewing a particular item
    def get_absolute_url(self):
        return reverse("item_detail", kwargs={'pk': self.pk})


from django.db import models

# Create your models here.

# article of clothing item
class Item(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    # idk how this works yet but this is probably what we need for images
    # image = models.ImageField(upload_to='')


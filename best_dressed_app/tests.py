from django.test import TestCase
from .models import *
# Create your tests here.

# test item model creation
class ItemModelTest(TestCase):
    def test_create_item(self):
        item = Item.objects.create(
            title="T shirt",
            description="A mind-bending thrilling T shirt the world has never seen",
            image_url = "https://coloradosprings.gov/sites/default/files/styles/large/public/2024-05/crystal_reservoir.jpg?itok=Z1jcwxG7"
        )

        # check entries
        created_item = Item.objects.get(title="T shirt")

        # Assertions: check that values match
        self.assertEqual(created_item.title, "T shirt")
        self.assertEqual(created_item.description, "A mind-bending thrilling T shirt the world has never seen")
        self.assertEqual(created_item.image_url,
                         "https://coloradosprings.gov/sites/default/files/styles/large/public/2024-05/crystal_reservoir.jpg?itok=Z1jcwxG7")
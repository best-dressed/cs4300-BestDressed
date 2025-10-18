from django.test import TestCase, Client
from .models import *
from django.urls import reverse
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


# test item listing views
# Heavily chatGPT based
# basically just simulate a bunch of requests and look for specific data that must have come from view logic
class ItemViewsTest(TestCase):
    def setUp(self):

        # make two dummy items to display on item_listing
        item = Item.objects.create(
            title="T shirt",
            description="A mind-bending thrilling T shirt the world has never seen",
            image_url = "https://coloradosprings.gov/sites/default/files/styles/large/public/2024-05/crystal_reservoir.jpg?itok=Z1jcwxG7"
        )
        item2 = Item.objects.create(
            title="Pants",
            description="One for each leg",
            image_url = "https://ashallendesign.co.uk/images/custom/short-url-logo.png"
        )

    def test_item_listing_view_status_code(self):
        """View should return 200 OK"""
        url = reverse("item_listing")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_item_listing_correct_template(self):
        """View should render the correct template"""
        url = reverse("item_listing")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "item_listing.html")

    def test_item_listing_displays_items(self):
        """View should include data about items in rendered HTML"""
        url = reverse("item_listing")
        response = self.client.get(url)
        self.assertContains(response, "T shirt")
        self.assertContains(response, "Pants")
        self.assertContains(response, "for each leg")
        self.assertContains(response, "https://ashallendesign.co.uk/images/custom/short-url-logo.png")

    def test_item_listing_view_context(self):
        """View should pass correct context data"""
        url = reverse("item_listing")
        response = self.client.get(url)
        self.assertIn("items", response.context)
        self.assertEqual(len(response.context["items"]), 2)
from django.test import TestCase, Client
from .models import *
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from best_dressed_app import views
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

    # test the single item listing view
    # using the first item primary key
    def test_item_detail_view_status_code(self):
        """View should return 200 OK"""
        item = Item.objects.create(
            title="Pants",
            description="One for each leg",
            image_url = "https://ashallendesign.co.uk/images/custom/short-url-logo.png"
        )
        pk = item.pk
        url = reverse("item_detail", kwargs={"pk": pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_item_detail_view_displays_item(self):
        """View should return 200 OK"""
        item = Item.objects.create(
            title="Pants",
            description="One for each leg",
            image_url = "https://ashallendesign.co.uk/images/custom/short-url-logo.png"
        )
        pk = item.pk
        url = reverse("item_detail", kwargs={"pk": pk})
        response = self.client.get(url)
        self.assertContains(response, "Pants")
        self.assertContains(response, "for each leg")
        self.assertContains(response, "https://ashallendesign.co.uk/images/custom/short-url-logo.png")
        # there should also be the other item we created in recommendations
        self.assertContains(response, "thrilling")
        self.assertContains(response, "T shirt")


# tests for landing page and after sign in page

class LandingPageTests(TestCase):
    # This test checks that when you go to the root URL Django correctly connects it to the index function.
    def test_root_url_resolves_to_index_view(self):
        match = resolve("/")
        self.assertIs(match.func, views.index)

    # This test makes sure that visitors who are not logged in see the normal public landing page aka index.html
    # It also checks that the page loads successfully aka status 200
    # and includes some expected text and buttons
    def test_index_anonymous_uses_index_template_and_has_cta(self):
        resp = self.client.get(reverse("index"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "../templates/index.html")
        self.assertContains(resp, "Build, Share, and Discover Outfits.")
        self.assertContains(resp, "Create account")
        self.assertContains(resp, "Log In")

   
   def test_index_authenticated_redirects_to_dashboard(self):
    """If logged in, visiting / should redirect to the dashboard"""
    User = get_user_model()
    user = User.objects.create_user(
        username="michal", email="m@example.com", password="pw12345!"
    )
    self.client.force_login(user)
    resp = self.client.get(reverse("index"))
    # Now logged-in users get redirected to the dashboard
    self.assertRedirects(resp, reverse("dashboard"))


class AuthRoutesExistTests(TestCase):
    # This test makes sure that the login page route even exists and loads
    def test_login_route_exists(self):
        resp = self.client.get(reverse("login"))
        self.assertEqual(resp.status_code, 200)

    # This test does the same for the create account route. it just confirms that the page exists and responds with the 200 ok
    def test_signup_route_exists(self):
        resp = self.client.get(reverse("signup"))
        self.assertEqual(resp.status_code, 200)
from django.test import TestCase, Client
from .models import *
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from best_dressed_app import views
from unittest.mock import Mock, patch, MagicMock
from best_dressed_app.recommendation import create_openai_client, prompt_ai, generate_recommendations
import openai
import os
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
        # updated expectation: logged-in users now redirect to dashboard
        self.assertRedirects(resp, reverse("dashboard"))



class AuthRoutesExistTests(TestCase):
    # This test makes sure that the login page route even exists and loads
    def test_login_route_exists(self):
        resp = self.client.get(reverse("login"))
        self.assertEqual(resp.status_code, 200)

    # This test does the same for the create account route. it just confirms that the page exists and responds with the 200 ok
    def test_signup_route_exists(self):
        resp = self.client.get(reverse("django_registration_register"))
        self.assertEqual(resp.status_code, 200)


# Tests for recommendation.py module
class CreateOpenAIClientTests(TestCase):
    """Tests for the create_openai_client function"""
    
    def test_create_client_with_valid_api_key(self):
        """Test that a client is created successfully with a valid API key"""
        api_key = "sk-test-key-123"
        
        # Check if OpenAI.OpenAI class exists (newer version)
        if hasattr(openai, "OpenAI"):
            client = create_openai_client(api_key)
            self.assertIsInstance(client, openai.OpenAI)
            self.assertEqual(client.api_key, api_key)
        else:
            # Older version - sets module-level api_key
            client = create_openai_client(api_key)
            self.assertEqual(client, openai)
            self.assertEqual(openai.api_key, api_key)
    
    def test_create_client_with_empty_api_key(self):
        """Test that ValueError is raised when API key is empty"""
        with self.assertRaises(ValueError) as context:
            create_openai_client("")
        self.assertIn("API key must be provided", str(context.exception))
    
    def test_create_client_with_none_api_key(self):
        """Test that ValueError is raised when API key is None"""
        with self.assertRaises(ValueError) as context:
            create_openai_client(None)
        self.assertIn("API key must be provided", str(context.exception))


class PromptAITests(TestCase):
    """Tests for the prompt_ai function"""
    
    @patch('openai.OpenAI')
    def test_prompt_ai_successful_response(self, mock_openai_class):
        """Test that prompt_ai returns the expected response from OpenAI"""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        
        # Configure mock chain
        mock_message.content = "  This is a test recommendation.  "
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test the function
        prompt = "Generate outfit recommendations"
        model = "gpt-4"
        result = prompt_ai(prompt, mock_client, model)
        
        # Assertions
        self.assertEqual(result, "This is a test recommendation.")
        mock_client.chat.completions.create.assert_called_once_with(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
    
    @patch('openai.OpenAI')
    def test_prompt_ai_with_different_model(self, mock_openai_class):
        """Test that prompt_ai works with different model names"""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        
        mock_message.content = "Response from GPT-3.5"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test with gpt-3.5-turbo
        prompt = "Test prompt"
        model = "gpt-3.5-turbo"
        result = prompt_ai(prompt, mock_client, model)
        
        self.assertEqual(result, "Response from GPT-3.5")
        mock_client.chat.completions.create.assert_called_once_with(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
    
    @patch('openai.OpenAI')
    def test_prompt_ai_strips_whitespace(self, mock_openai_class):
        """Test that prompt_ai properly strips leading/trailing whitespace"""
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        
        # Response with lots of whitespace
        mock_message.content = "\n\n  Test response with whitespace  \n\n"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        result = prompt_ai("Test", mock_client, "gpt-4")
        self.assertEqual(result, "Test response with whitespace")


# class GenerateRecommendationsTests(TestCase):
#     """Tests for the generate_recommendations function"""
#
#     def setUp(self):
#         """Set up test fixtures"""
#         # Create a test user
#         User = get_user_model()
#         self.user = User.objects.create_user(
#             username='testuser',
#             password='testpass123'
#         )
#
#         # Create a user profile
#         self.user_profile = UserProfile.objects.create(
#             user=self.user,
#             bio="I love casual and comfortable clothes",
#             style_preferences="casual, streetwear",
#             favorite_colors="blue, black, white"
#         )
#
#     @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key-123'})
#     @patch('best_dressed_app.recommendation.create_openai_client')
#     @patch('best_dressed_app.recommendation.prompt_ai')
#     def test_generate_recommendations_success(self, mock_prompt_ai, mock_create_client):
#         """Test successful recommendation generation"""
#         # Setup mocks
#         mock_client = Mock()
#         mock_create_client.return_value = mock_client
#         mock_prompt_ai.return_value = "Here are your personalized recommendations: 1. Blue jeans 2. Black hoodie"
#
#         available_items = "T-shirts, jeans, hoodies, sneakers"
#
#         # Call function
#         result = generate_recommendations(available_items, self.user_profile)
#
#         # Assertions
#         self.assertEqual(result, "Here are your personalized recommendations: 1. Blue jeans 2. Black hoodie")
#         mock_create_client.assert_called_once_with('sk-test-key-123')
#         mock_prompt_ai.assert_called_once()
#
#         # Verify the prompt contains user profile information
#         call_args = mock_prompt_ai.call_args
#         prompt_text = call_args[0][0]
#         self.assertIn(self.user_profile.bio, prompt_text)
#         self.assertIn(self.user_profile.style_preferences, prompt_text)
#         self.assertIn(self.user_profile.favorite_colors, prompt_text)
#         self.assertIn(available_items, prompt_text)
#
#     @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key-123'})
#     @patch('best_dressed_app.recommendation.create_openai_client')
#     @patch('best_dressed_app.recommendation.prompt_ai')
#     def test_generate_recommendations_uses_correct_model(self, mock_prompt_ai, mock_create_client):
#         """Test that the function uses gpt-4 model"""
#         mock_client = Mock()
#         mock_create_client.return_value = mock_client
#         mock_prompt_ai.return_value = "Recommendations"
#
#         available_items = "Various items"
#         generate_recommendations(available_items, self.user_profile)
#
#         # Check that prompt_ai was called with gpt-4 model
#         call_args = mock_prompt_ai.call_args
#         self.assertEqual(call_args[0][2], "gpt-4")  # Third argument is the model
#
#     @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key-123'})
#     @patch('best_dressed_app.recommendation.create_openai_client')
#     @patch('best_dressed_app.recommendation.prompt_ai')
#     def test_generate_recommendations_error_handling(self, mock_prompt_ai, mock_create_client):
#         """Test that errors are caught and proper error message is returned"""
#         # Setup mock to raise an exception
#         mock_client = Mock()
#         mock_create_client.return_value = mock_client
#         mock_prompt_ai.side_effect = Exception("API Error")
#
#         available_items = "T-shirts, jeans"
#
#         # Call function
#         result = generate_recommendations(available_items, self.user_profile)
#
#         # Should return error message instead of raising exception
#         self.assertEqual(result, "Error generating recommendations.")
#
#     @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key-123'})
#     @patch('best_dressed_app.recommendation.create_openai_client')
#     @patch('best_dressed_app.recommendation.prompt_ai')
#     def test_generate_recommendations_with_empty_available_items(self, mock_prompt_ai, mock_create_client):
#         """Test recommendation generation when no items are available"""
#         mock_client = Mock()
#         mock_create_client.return_value = mock_client
#         mock_prompt_ai.return_value = "No items available for recommendations."
#
#         available_items = ""
#         result = generate_recommendations(available_items, self.user_profile)
#
#         # Should still call the API and return a response
#         self.assertEqual(result, "No items available for recommendations.")
#         mock_prompt_ai.assert_called_once()
#
#     @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key-123'})
#     @patch('best_dressed_app.recommendation.create_openai_client')
#     @patch('best_dressed_app.recommendation.prompt_ai')
#     def test_generate_recommendations_prompt_format(self, mock_prompt_ai, mock_create_client):
#         """Test that the prompt is formatted correctly and doesn't use user's name"""
#         mock_client = Mock()
#         mock_create_client.return_value = mock_client
#         mock_prompt_ai.return_value = "Recommendations"
#
#         available_items = "Shirts and pants"
#         generate_recommendations(available_items, self.user_profile)
#
#         # Get the prompt that was sent
#         call_args = mock_prompt_ai.call_args
#         prompt_text = call_args[0][0]
#
#         # Check that prompt contains expected elements
#         self.assertIn("fashion recommendation engine", prompt_text.lower())
#         self.assertIn("User Bio:", prompt_text)
#         self.assertIn("Style Preferences:", prompt_text)
#         self.assertIn("Favorite Colors:", prompt_text)
#         self.assertIn("Available Items:", prompt_text)
#
#         # Verify it tells AI not to use username
#         self.assertIn('Do not use the user\'s name or username', prompt_text)
#         self.assertIn('only use "you" instead', prompt_text)
#
#     @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key-123'})
#     @patch('best_dressed_app.recommendation.create_openai_client')
#     @patch('best_dressed_app.recommendation.prompt_ai')
#     def test_generate_recommendations_with_special_characters(self, mock_prompt_ai, mock_create_client):
#         """Test that special characters in user profile are handled correctly"""
#         # Create profile with special characters
#         self.user_profile.bio = "I love clothes with 'quotes' and \"double quotes\""
#         self.user_profile.style_preferences = "edgy & bold"
#         self.user_profile.favorite_colors = "red, green, blue"
#         self.user_profile.save()
#
#         mock_client = Mock()
#         mock_create_client.return_value = mock_client
#         mock_prompt_ai.return_value = "Edgy recommendations"
#
#         available_items = "Leather jackets & boots"
#         result = generate_recommendations(available_items, self.user_profile)
#
#         # Should handle special characters without errors
#         self.assertEqual(result, "Edgy recommendations")
#         mock_prompt_ai.assert_called_once()

# some chatGPT stuff that seems to work good enough
from unittest.mock import patch, Mock
from django.test import TestCase
from django.contrib.auth import get_user_model
from best_dressed_app.models import UserProfile, Item
from best_dressed_app.recommendation import generate_recommendations

class GenerateRecommendationsTests(TestCase):
    """Tests for the generate_recommendations function"""

    def setUp(self):
        """Set up test user, profile, and sample items"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.user_profile = UserProfile.objects.create(
            user=self.user,
            bio="I love casual and comfortable clothes",
            style_preferences="casual, streetwear",
            favorite_colors="blue, black, white"
        )

        # Create sample Item objects
        self.item1 = Item.objects.create(
            title="Blue Jeans",
            description="Comfortable denim jeans",
            tag="Legs"
        )
        self.item2 = Item.objects.create(
            title="Black Hoodie",
            description="Warm cotton hoodie",
            tag="Torso"
        )
        self.item3 = Item.objects.create(
            title="White Sneakers",
            description="Stylish casual shoes",
            tag="Shoes"
        )

        self.items_list = [self.item1, self.item2, self.item3]

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test-key-123'})
    @patch('best_dressed_app.recommendation.create_openai_client')
    @patch('best_dressed_app.recommendation.prompt_ai')
    def test_generate_recommendations_success(self, mock_prompt_ai, mock_create_client):
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        mock_prompt_ai.return_value = "Here are your personalized recommendations: 1. Blue Jeans 2. Black Hoodie"

        result = generate_recommendations(self.items_list, self.user_profile)

        self.assertEqual(result, "Here are your personalized recommendations: 1. Blue Jeans 2. Black Hoodie")
        mock_create_client.assert_called_once_with('sk-test-key-123')
        mock_prompt_ai.assert_called_once()

        prompt_text = mock_prompt_ai.call_args[0][0]
        self.assertIn(self.user_profile.bio, prompt_text)
        self.assertIn(self.user_profile.style_preferences, prompt_text)
        self.assertIn(self.user_profile.favorite_colors, prompt_text)
        # Check that item info is in the prompt
        self.assertIn(self.item1.title, prompt_text)
        self.assertIn(self.item2.title, prompt_text)
        self.assertIn(self.item3.title, prompt_text)

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test-key-123'})
    @patch('best_dressed_app.recommendation.create_openai_client')
    @patch('best_dressed_app.recommendation.prompt_ai')
    def test_generate_recommendations_uses_correct_model(self, mock_prompt_ai, mock_create_client):
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        mock_prompt_ai.return_value = "Recommendations"

        generate_recommendations(self.items_list, self.user_profile)

        call_args = mock_prompt_ai.call_args

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test-key-123'})
    @patch('best_dressed_app.recommendation.create_openai_client')
    @patch('best_dressed_app.recommendation.prompt_ai')
    def test_generate_recommendations_error_handling(self, mock_prompt_ai, mock_create_client):
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        mock_prompt_ai.side_effect = Exception("API Error")

        result = generate_recommendations(self.items_list, self.user_profile)
        self.assertEqual(result, "Error generating recommendations.")

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test-key-123'})
    @patch('best_dressed_app.recommendation.create_openai_client')
    @patch('best_dressed_app.recommendation.prompt_ai')
    def test_generate_recommendations_with_empty_available_items(self, mock_prompt_ai, mock_create_client):
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        mock_prompt_ai.return_value = "No items available for recommendations."

        result = generate_recommendations([], self.user_profile)
        self.assertEqual(result, "No items available for recommendations.")
        mock_prompt_ai.assert_called_once()

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test-key-123'})
    @patch('best_dressed_app.recommendation.create_openai_client')
    @patch('best_dressed_app.recommendation.prompt_ai')
    def test_generate_recommendations_prompt_format(self, mock_prompt_ai, mock_create_client):
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        mock_prompt_ai.return_value = "Recommendations"

        generate_recommendations(self.items_list, self.user_profile)

        prompt_text = mock_prompt_ai.call_args[0][0]
        self.assertIn("fashion recommendation engine", prompt_text.lower())
        self.assertIn("User Bio:", prompt_text)
        self.assertIn("Style Preferences:", prompt_text)
        self.assertIn("Favorite Colors:", prompt_text)
        self.assertIn("Available Items", prompt_text)
        self.assertIn("Do not use the user's name or username", prompt_text)
        self.assertIn('only use "you" instead', prompt_text)

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test-key-123'})
    @patch('best_dressed_app.recommendation.create_openai_client')
    @patch('best_dressed_app.recommendation.prompt_ai')
    def test_generate_recommendations_with_special_characters(self, mock_prompt_ai, mock_create_client):
        self.user_profile.bio = "I love clothes with 'quotes' and \"double quotes\""
        self.user_profile.style_preferences = "edgy & bold"
        self.user_profile.favorite_colors = "red, green, blue"
        self.user_profile.save()

        mock_client = Mock()
        mock_create_client.return_value = mock_client
        mock_prompt_ai.return_value = "Edgy recommendations"

        result = generate_recommendations(self.items_list, self.user_profile)
        self.assertEqual(result, "Edgy recommendations")
        mock_prompt_ai.assert_called_once()
"""
Comprehensive test suite for AI Recommendations feature.

This test file covers:
- Recommendation model creation and relationships
- Saving AI recommendations to database
- Fetching and displaying recommendation history
- Security: users only see their own recommendations
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from best_dressed_app.models import Item, UserProfile, SavedRecommendation
from unittest.mock import patch, MagicMock
import json


class SavedRecommendationModelTests(TestCase):
    """Tests for the SavedRecommendation model"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create some catalog items
        self.item1 = Item.objects.create(
            title="Blue Jeans",
            description="Classic blue denim jeans",
            tag="legs"
        )
        self.item2 = Item.objects.create(
            title="White T-Shirt",
            description="Plain white cotton t-shirt",
            tag="torso"
        )
    
    def test_create_saved_recommendation(self):
        """Test creating a SavedRecommendation instance"""
        recommendation = SavedRecommendation.objects.create(
            user=self.user,
            prompt="I need casual summer outfits",
            ai_response="Here are some great summer outfit ideas..."
        )
        
        self.assertEqual(recommendation.user, self.user)
        self.assertEqual(recommendation.prompt, "I need casual summer outfits")
        self.assertIn("summer", recommendation.ai_response)
        self.assertIsNotNone(recommendation.created_at)
    
    def test_saved_recommendation_with_items(self):
        """Test SavedRecommendation with recommended items"""
        recommendation = SavedRecommendation.objects.create(
            user=self.user,
            prompt="Business casual outfit",
            ai_response="Professional yet comfortable..."
        )
        
        # Add recommended items
        recommendation.recommended_items.add(self.item1, self.item2)
        
        self.assertEqual(recommendation.item_count(), 2)
        self.assertIn(self.item1, recommendation.recommended_items.all())
        self.assertIn(self.item2, recommendation.recommended_items.all())
    
    def test_saved_recommendation_str_method(self):
        """Test the string representation of SavedRecommendation"""
        recommendation = SavedRecommendation.objects.create(
            user=self.user,
            prompt="I need a long prompt that will be truncated in the string representation",
            ai_response="Some response"
        )
        
        str_repr = str(recommendation)
        self.assertIn(self.user.username, str_repr)
        self.assertTrue(len(recommendation.prompt[:50]) <= 50)
    
    def test_saved_recommendation_ordering(self):
        """Test that recommendations are ordered by created_at descending"""
        rec1 = SavedRecommendation.objects.create(
            user=self.user,
            prompt="First recommendation",
            ai_response="Response 1"
        )
        rec2 = SavedRecommendation.objects.create(
            user=self.user,
            prompt="Second recommendation",
            ai_response="Response 2"
        )
        rec3 = SavedRecommendation.objects.create(
            user=self.user,
            prompt="Third recommendation",
            ai_response="Response 3"
        )
        
        recommendations = SavedRecommendation.objects.all()
        
        # Should be in reverse chronological order
        self.assertEqual(recommendations[0], rec3)
        self.assertEqual(recommendations[1], rec2)
        self.assertEqual(recommendations[2], rec1)
    
    def test_cascade_delete_user(self):
        """Test that recommendations are deleted when user is deleted"""
        SavedRecommendation.objects.create(
            user=self.user,
            prompt="Test prompt",
            ai_response="Test response"
        )
        
        self.assertEqual(SavedRecommendation.objects.filter(user=self.user).count(), 1)
        
        # Delete user
        self.user.delete()
        
        # Recommendation should be deleted too
        self.assertEqual(SavedRecommendation.objects.count(), 0)
    
    def test_multiple_users_recommendations(self):
        """Test that recommendations are properly separated by user"""
        User = get_user_model()
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Create recommendations for both users
        rec1 = SavedRecommendation.objects.create(
            user=self.user,
            prompt="User 1 prompt",
            ai_response="Response 1"
        )
        rec2 = SavedRecommendation.objects.create(
            user=user2,
            prompt="User 2 prompt",
            ai_response="Response 2"
        )
        
        # Each user should only see their own recommendations
        user1_recs = SavedRecommendation.objects.filter(user=self.user)
        user2_recs = SavedRecommendation.objects.filter(user=user2)
        
        self.assertEqual(user1_recs.count(), 1)
        self.assertEqual(user2_recs.count(), 1)
        self.assertIn(rec1, user1_recs)
        self.assertIn(rec2, user2_recs)


class RecommendationsViewTests(TestCase):
    """Tests for the recommendations view"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        
        # Create user profile
        UserProfile.objects.create(
            user=self.user,
            style_preferences="casual",
            favorite_colors="blue, green"
        )
        
        # Create some saved recommendations
        self.rec1 = SavedRecommendation.objects.create(
            user=self.user,
            prompt="Summer outfits",
            ai_response="Here are great summer options..."
        )
        self.rec2 = SavedRecommendation.objects.create(
            user=self.user,
            prompt="Business casual",
            ai_response="Professional recommendations..."
        )
    
    def test_recommendations_requires_authentication(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client.get(reverse('recommendations'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_recommendations_loads_for_authenticated_user(self):
        """Test that authenticated users can access recommendations page"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('recommendations'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recommendations.html')
    
    def test_recommendations_shows_history(self):
        """Test that past recommendations are displayed"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('recommendations'))
        
        # Check that recommendations are in context
        self.assertIn('past_recommendations', response.context)
        past_recs = response.context['past_recommendations']
        
        self.assertEqual(len(past_recs), 2)
        self.assertIn(self.rec1, past_recs)
        self.assertIn(self.rec2, past_recs)
    
    def test_recommendations_ordered_newest_first(self):
        """Test that recommendations are ordered with newest first"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('recommendations'))
        
        past_recs = response.context['past_recommendations']
        
        # rec2 was created last, so should be first
        self.assertEqual(past_recs[0], self.rec2)
        self.assertEqual(past_recs[1], self.rec1)
    
    def test_user_only_sees_own_recommendations(self):
        """Test that users only see their own recommendations"""
        User = get_user_model()
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Create recommendation for user2
        rec3 = SavedRecommendation.objects.create(
            user=user2,
            prompt="User 2 prompt",
            ai_response="User 2 response"
        )
        
        # Login as user1
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('recommendations'))
        
        past_recs = response.context['past_recommendations']
        
        # Should only see user1's recommendations
        self.assertEqual(len(past_recs), 2)
        self.assertNotIn(rec3, past_recs)


class GenerateRecommendationsAjaxTests(TestCase):
    """Tests for the AJAX recommendation generation endpoint"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        
        # Create user profile
        self.profile = UserProfile.objects.create(
            user=self.user,
            style_preferences="casual",
            favorite_colors="blue"
        )
        
        # Create catalog items
        self.item1 = Item.objects.create(
            id=1,
            title="Blue Jeans",
            description="Classic blue denim jeans",
            tag="legs"
        )
        self.item2 = Item.objects.create(
            id=2,
            title="White T-Shirt",
            description="Plain white cotton t-shirt",
            tag="torso"
        )
    
    def test_ajax_requires_authentication(self):
        """Test that AJAX endpoint requires authentication"""
        response = self.client.post(
            reverse('generate_recommendations_ajax'),
            data=json.dumps({'prompt': 'test prompt'}),
            content_type='application/json'
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_ajax_requires_post_method(self):
        """Test that endpoint only accepts POST requests"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('generate_recommendations_ajax'))
        
        self.assertEqual(response.status_code, 405)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('POST', data['error'])
    
    def test_ajax_requires_prompt(self):
        """Test that endpoint requires a prompt"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('generate_recommendations_ajax'),
            data=json.dumps({'prompt': ''}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('prompt', data['error'].lower())
    
    @patch('best_dressed_app.views.generate_recommendations')
    def test_ajax_saves_recommendation_to_database(self, mock_generate):
        """Test that successful generation saves to database"""
        # Mock the AI response
        mock_generate.return_value = "Great recommendations!\nRECOMMENDED_ITEMS: [1, 2]"
        
        self.client.login(username='testuser', password='testpass123')
        
        # Verify no recommendations exist yet
        self.assertEqual(SavedRecommendation.objects.count(), 0)
        
        response = self.client.post(
            reverse('generate_recommendations_ajax'),
            data=json.dumps({'prompt': 'casual summer outfits'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Check that recommendation was saved
        self.assertEqual(SavedRecommendation.objects.count(), 1)
        saved_rec = SavedRecommendation.objects.first()
        
        self.assertEqual(saved_rec.user, self.user)
        self.assertEqual(saved_rec.prompt, 'casual summer outfits')
        self.assertIn('Great recommendations', saved_rec.ai_response)
        
        # Check that items were associated
        self.assertEqual(saved_rec.item_count(), 2)
        self.assertIn(self.item1, saved_rec.recommended_items.all())
        self.assertIn(self.item2, saved_rec.recommended_items.all())
    
    @patch('best_dressed_app.views.generate_recommendations')
    def test_ajax_returns_success_response(self, mock_generate):
        """Test that successful generation returns proper JSON response"""
        mock_generate.return_value = "Here are recommendations\nRECOMMENDED_ITEMS: [1, 2]"
        
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('generate_recommendations_ajax'),
            data=json.dumps({'prompt': 'test prompt'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertIn('recommendations', data)
        self.assertIn('items', data)
        self.assertEqual(len(data['items']), 2)
    
    @patch('best_dressed_app.views.generate_recommendations')
    def test_ajax_handles_no_items_in_response(self, mock_generate):
        """Test handling when AI doesn't recommend specific items"""
        mock_generate.return_value = "General fashion advice without specific items"
        
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('generate_recommendations_ajax'),
            data=json.dumps({'prompt': 'fashion tips'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['items']), 0)
        
        # Should still save the recommendation
        self.assertEqual(SavedRecommendation.objects.count(), 1)
        saved_rec = SavedRecommendation.objects.first()
        self.assertEqual(saved_rec.item_count(), 0)
    
    def test_ajax_handles_missing_user_profile(self):
        """Test error handling when user profile doesn't exist"""
        User = get_user_model()
        user_no_profile = User.objects.create_user(
            username='noprofile',
            password='testpass123'
        )
        
        self.client.login(username='noprofile', password='testpass123')
        
        response = self.client.post(
            reverse('generate_recommendations_ajax'),
            data=json.dumps({'prompt': 'test'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('profile', data['error'].lower())
    
    @patch('best_dressed_app.views.generate_recommendations')
    def test_ajax_handles_generation_error(self, mock_generate):
        """Test error handling when AI generation fails"""
        mock_generate.side_effect = Exception("API error")
        
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('generate_recommendations_ajax'),
            data=json.dumps({'prompt': 'test'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        
        # Should not save failed recommendation
        self.assertEqual(SavedRecommendation.objects.count(), 0)

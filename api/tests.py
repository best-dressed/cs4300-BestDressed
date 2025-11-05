# all credit to ChatGPT on here

from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.http import JsonResponse
import os
import base64
import json
from best_dressed_app.models import Item

# Set environment variables for testing
os.environ['EBAY_VERIFICATION_TOKEN'] = 'test_verification_token'
os.environ['EBAY_BASE64_AUTHORIZATION_TOKEN'] = 'dGVzdF9iYXNlNjRfYXV0aF90b2tlbg=='  # base64 test token

class EbayViewsTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def test_challenge_code_response(self):
        # Simulate GET request with challenge_code
        response = self.client.get(
            reverse('ebay_market_delete') + '?challenge_code=test123'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('challengeResponse', data)
        # Ensure the response is a 64-character hex string (SHA256)
        self.assertEqual(len(data['challengeResponse']), 64)

    @patch('api.views.get_oath_token', return_value='fake_token')
    @patch('requests.get')
    def test_ebay_get_items_post_creates_items(self, mock_get, mock_token):
        # Mock eBay search response
        mock_search_response = {
            "itemSummaries": [
                {
                    "itemId": "123",
                    "title": "Test Item",
                    "price": {"value": "10.00", "currency": "USD"},
                    "seller": {"username": "seller1"},
                    "itemWebUrl": "http://example.com/item/123",
                    "image": {"imageUrl": "http://example.com/image.jpg"}
                }
            ]
        }

        mock_detail_response = {
            "shortDescription": "Test description"
        }

        # Mock sequential requests: search then item detail
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_search_response),
            MagicMock(status_code=200, json=lambda: mock_detail_response)
        ]

        response = self.client.post(
            reverse('ebay_get_items'),
            data={'search_term': 'Test', 'item_count': 1}
        )

        # Should render template with form and recent_items
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ebay_add_item.html')
        self.assertTrue(Item.objects.filter(title='Test Item').exists())
        item = Item.objects.get(title='Test Item')
        self.assertEqual(item.description, 'Test description')
        self.assertEqual(item.tag, 'Accessory')

    def test_ebay_get_items_get_request(self):
        # GET request should return empty form and template
        response = self.client.get(reverse('ebay_get_items'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ebay_add_item.html')
        self.assertIn('form', response.context)

# chatGPT with small tweaks

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
        """
        ✅ Tests GET /auth/ebay_market_delete/?challenge_code=...
        Ensures proper challengeResponse SHA256 hash is returned.
        """
        response = self.client.get(
            reverse('ebay_market_delete') + '?challenge_code=test123'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('challengeResponse', data)
        self.assertEqual(len(data['challengeResponse']), 64)

    @patch('api.views.get_oath_token', return_value='fake_token')
    @patch('requests.get')
    def test_post_invalid_signature_returns_412(self, mock_get, mock_token):
        """
        ✅ Tests POST /auth/ebay_market_delete/ with an invalid signature.
        Mocks public key fetch and forces InvalidSignature branch.
        """
        fake_public_key = """-----BEGIN PUBLIC KEY-----
MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAEz2dK6S0RZKoF7zT9f3v7UzE1kmD+YvXY
J0LxQzV2ZyJpi1Pz+nKTmPnF/cTxN9Z+KxJ7Fv+7iCV6VpplJj+s/Q==
-----END PUBLIC KEY-----"""
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {'key': fake_public_key})

        # Prepare fake POST data and headers
        body = json.dumps({'dummy': 'data'}).encode('utf-8')
        signature_dict = {'kid': 'fake_kid', 'signature': base64.b64encode(b'bad_signature').decode('utf-8')}
        headers = {'HTTP_X_EBAY_SIGNATURE': base64.b64encode(json.dumps(signature_dict).encode('utf-8')).decode('utf-8')}

        response = self.client.post(
            reverse('ebay_market_delete'),
            data=body,
            content_type='application/json',
            **headers
        )

        self.assertEqual(response.status_code, 412)
        self.assertJSONEqual(response.content, {'error': 'Invalid public key or Signature'})

    @patch('api.views.get_oath_token', return_value='fake_token')
    @patch('requests.get')
    def test_ebay_get_items_post_creates_items(self, mock_get, mock_token):
        """
        ✅ Tests POST /ebay_add_items/ to ensure items are created and parsed.
        """
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

        mock_detail_response = {"shortDescription": "Test description"}

        # Sequential requests: search then item detail
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_search_response),
            MagicMock(status_code=200, json=lambda: mock_detail_response)
        ]

        response = self.client.post(
            reverse('ebay_get_items'),
            data={'search_term': 'Test', 'item_count': 1}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ebay_add_item.html')
        self.assertTrue(Item.objects.filter(title='Test Item').exists())

        item = Item.objects.get(title='Test Item')
        self.assertEqual(item.description, 'Test description')
        self.assertEqual(item.tag, 'Accessory')

    def test_ebay_get_items_get_request(self):
        """
        ✅ Tests GET /ebay_add_items/ ensures empty form and template render.
        """
        response = self.client.get(reverse('ebay_get_items'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ebay_add_item.html')
        self.assertIn('form', response.context)

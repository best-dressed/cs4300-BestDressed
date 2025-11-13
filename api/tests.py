# chatGPT with small tweaks

from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from unittest.mock import patch, MagicMock
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from django.http import JsonResponse
import os
import base64
import logging
import json
from best_dressed_app.models import Item
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

# Set environment variables for testing
os.environ['EBAY_VERIFICATION_TOKEN'] = 'test_verification_token'
os.environ['EBAY_BASE64_AUTHORIZATION_TOKEN'] = 'dGVzdF9iYXNlNjRfYXV0aF90b2tlbg=='  # base64 test token

class EbayViewsTestCase(TestCase):

    def setUp(self):

        # create a user so we can access login only views
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

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

from api.views import ebay_marketplace_deletion_notification


class EbaySignatureValidationSuccessTest(TestCase):
    """
    ✅ Tests that a valid eBay signature passes verification successfully.
    """

    def setUp(self):
        self.factory = RequestFactory()

        # Generate ECDSA key pair
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()

        # Export PEM public key to simulate eBay's returned key
        self.public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")

        # Example JSON message body
        self.fake_body = json.dumps({
            "user_id": "12345",
            "action": "delete"
        }).encode("utf-8")

        # Sign message using private key (ECDSA with SHA1)
        signature = self.private_key.sign(self.fake_body, ec.ECDSA(hashes.SHA1()))

        # Build eBay-style signature header
        encoded_signature = base64.b64encode(signature).decode("utf-8")
        header_json = json.dumps({
            "kid": "test_key_id",
            "signature": encoded_signature
        }).encode("utf-8")
        self.encoded_header = base64.b64encode(header_json).decode("utf-8")

    @patch("api.views.requests.get")
    @patch("api.views.get_oath_token", return_value="fake_token")
    def test_valid_signature_returns_200(self, mock_token, mock_get):
        """
        Ensures that a correctly signed request returns HTTP 200.
        """
        # Mock the public key fetch
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"key": self.public_key_pem}

        # Build fake POST request
        request = self.factory.post(
            "/auth/ebay_market_delete/",
            data=self.fake_body,
            content_type="application/json",
            HTTP_X_EBAY_SIGNATURE=self.encoded_header
        )

        # Call the actual view
        logger.warning("CALLING EBAY MARKET DELETE")
        response = ebay_marketplace_deletion_notification(request)

        # Expect success
        self.assertEqual(response.status_code, 200)
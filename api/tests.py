# chatGPT with full coverage additions

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
    """Tests for eBay views including marketplace deletion and item fetching."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

    def test_challenge_code_response(self):
        """Test GET /auth/ebay_market_delete/?challenge_code=..."""
        response = self.client.get(reverse('ebay_market_delete') + '?challenge_code=test123')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('challengeResponse', data)
        self.assertEqual(len(data['challengeResponse']), 64)

    @patch('api.views.get_oath_token', return_value='fake_token')
    @patch('requests.get')
    def test_post_invalid_signature_returns_412(self, mock_get, mock_token):
        """Test invalid signature handling in POST /auth/ebay_market_delete/"""
        fake_public_key = """-----BEGIN PUBLIC KEY-----
MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAEz2dK6S0RZKoF7zT9f3v7UzE1kmD+YvXY
J0LxQzV2ZyJpi1Pz+nKTmPnF/cTxN9Z+KxJ7Fv+7iCV6VpplJj+s/Q==
-----END PUBLIC KEY-----"""
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {'key': fake_public_key})

        body = json.dumps({'dummy': 'data'}).encode('utf-8')
        signature_dict = {'kid': 'fake_kid', 'signature': base64.b64encode(b'bad_signature').decode('utf-8')}
        headers = {'HTTP_X_EBAY_SIGNATURE': base64.b64encode(json.dumps(signature_dict).encode('utf-8')).decode('utf-8')}

        response = self.client.post(reverse('ebay_market_delete'), data=body, content_type='application/json', **headers)

        self.assertEqual(response.status_code, 412)
        self.assertJSONEqual(response.content, {'error': 'Invalid public key or Signature'})

    @patch('api.views.get_oath_token', return_value='fake_token')
    @patch('requests.get')
    def test_ebay_get_items_post_parses_items_correctly(self, mock_get, mock_token):
        """Test POST /ebay_add_items/ parses items into context without DB save"""
        mock_search_response = {
            "itemSummaries": [{"itemId": "123", "title": "Test Item", "price": {"value": "10.00", "currency": "USD"}, "seller": {"username": "seller1"}, "itemWebUrl": "http://example.com/item/123"}]
        }
        mock_detail_response = {"shortDescription": "Test description", "seller": {"sellerId": "seller1"}, "image": {"imageUrl": "http://example.com/img.jpg"}}
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_search_response),
            MagicMock(status_code=200, json=lambda: mock_detail_response)
        ]

        response = self.client.post(reverse('ebay_get_items'), data={'search_term': 'Test', 'item_count': 1})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ebay_add_item.html')
        self.assertIn('recent_items', response.context)
        self.assertEqual(len(response.context['recent_items']), 1)

        parsed_item = response.context['recent_items'][0]
        self.assertEqual(parsed_item['title'], "Test Item")
        self.assertEqual(parsed_item['description'], "Test description")
        self.assertEqual(parsed_item['seller_id'], "seller1")
        self.assertEqual(parsed_item['item_url'], "http://example.com/item/123")
        self.assertEqual(parsed_item['image_url'], "http://example.com/img.jpg")
        self.assertFalse(Item.objects.exists())

    def test_ebay_get_items_get_request(self):
        """Test GET /ebay_add_items/ returns empty form"""
        response = self.client.get(reverse('ebay_get_items'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ebay_add_item.html')
        self.assertIn('form', response.context)

    # -------------------------
    # Full coverage eBay deletion
    # -------------------------
    @patch('api.views.serialization.load_pem_public_key')
    @patch('api.views.requests.get')
    @patch('api.views.get_oath_token', return_value='fake_token')
    def test_ebay_deletion_removes_items_with_matching_seller_id(self, mock_get_oauth, mock_requests_get, mock_load_key):
        """Ensures deletion webhook removes Items with matching seller_id"""
        item1 = Item.objects.create(title="Item A", description="desc", image_url="http://img/a", tag="Accessory", item_id="111", seller_id="delete_me")
        item2 = Item.objects.create(title="Item B", description="desc", image_url="http://img/b", tag="Accessory", item_id="222", seller_id="keep_me")

        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {"key": "-----BEGIN PUBLIC KEY-----\nfake\n-----END PUBLIC KEY-----"}

        fake_key = MagicMock()
        fake_key.verify = MagicMock(return_value=None)
        mock_load_key.return_value = fake_key

        fake_sig = base64.b64encode(json.dumps({"kid": "fake", "signature": base64.b64encode(b'abc').decode()}).encode()).decode()
        payload = {"username": "delete_me"}

        response = self.client.post(reverse('ebay_market_delete'), data=json.dumps(payload), content_type="application/json", HTTP_X_EBAY_SIGNATURE=fake_sig)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Item.objects.filter(id=item1.id).exists())
        self.assertTrue(Item.objects.filter(id=item2.id).exists())

    # -------------------------
    # Additional branches for coverage
    # -------------------------
    @patch('api.views.requests.get')
    @patch('api.views.serialization.load_pem_public_key', side_effect=ValueError("Invalid PEM"))
    @patch('api.views.get_oath_token', return_value='fake_token')
    def test_invalid_public_key_returns_412(self, mock_token, mock_load_key, mock_requests_get):
        """
        Branch: public key deserialization fails
        """
        # mock fetch returns ANY string (the value will fail deserialization)
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {"key": "INVALID_KEY_STRING"}

        fake_sig = base64.b64encode(json.dumps({
            "kid": "fake",
            "signature": base64.b64encode(b"abc").decode()
        }).encode()).decode()

        payload = {"username": "delete_me"}

        response = self.client.post(
            reverse('ebay_market_delete'),
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_EBAY_SIGNATURE=fake_sig
        )

        self.assertEqual(response.status_code, 412)
        self.assertJSONEqual(response.content, {'error': 'Invalid public key or Signature'})

    @patch('api.views.serialization.load_pem_public_key')
    @patch('api.views.requests.get', side_effect=Exception("PK fetch failed"))
    @patch('api.views.get_oath_token', return_value='fake_token')
    def test_public_key_fetch_exception_returns_500(self, mock_get_oauth, mock_requests_get, mock_load_key):
        """Branch: exception during public key fetch"""
        fake_sig = base64.b64encode(json.dumps({"kid": "fake", "signature": base64.b64encode(b'abc').decode()}).encode()).decode()
        payload = {"username": "someone"}
        response = self.client.post(reverse('ebay_market_delete'), data=json.dumps(payload), content_type="application/json", HTTP_X_EBAY_SIGNATURE=fake_sig)
        self.assertEqual(response.status_code, 500)

    @patch('api.views.requests.get')
    @patch('api.views.serialization.load_pem_public_key')
    @patch('api.views.get_oath_token', return_value='fake_token')
    def test_missing_username_in_payload(self, mock_token, mock_load_key, mock_requests_get):
        """
        Branch: payload missing 'username' field
        """
        # mock public key returns a valid key (so we pass signature verification)
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {
            "key": "-----BEGIN PUBLIC KEY-----\nFAKE_KEY\n-----END PUBLIC KEY-----"
        }

        # Mock load_pem_public_key to return a fake key object whose verify() does nothing
        fake_key = MagicMock()
        fake_key.verify = MagicMock(return_value=None)
        mock_load_key.return_value = fake_key

        fake_sig = base64.b64encode(json.dumps({
            "kid": "fake",
            "signature": base64.b64encode(b"abc").decode()
        }).encode()).decode()

        payload = {}  # No username

        response = self.client.post(
            reverse('ebay_market_delete'),
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_EBAY_SIGNATURE=fake_sig
        )

        self.assertEqual(response.status_code, 200)
        # Confirm it logged the missing username but did not crash
        # Optionally check the log or response content if you modify the view to return a message

# -----------------------
# Existing signature test
# -----------------------
from api.views import ebay_marketplace_deletion_notification

class EbaySignatureValidationSuccessTest(TestCase):
    """Tests valid eBay signature paths."""

    def setUp(self):
        self.factory = RequestFactory()
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
        self.public_key_pem = self.public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8")
        self.fake_body = json.dumps({"user_id": "12345", "action": "delete"}).encode("utf-8")
        signature = self.private_key.sign(self.fake_body, ec.ECDSA(hashes.SHA1()))
        encoded_signature = base64.b64encode(signature).decode("utf-8")
        header_json = json.dumps({"kid": "test_key_id", "signature": encoded_signature}).encode("utf-8")
        self.encoded_header = base64.b64encode(header_json).decode("utf-8")

    @patch("api.views.requests.get")
    @patch("api.views.get_oath_token", return_value="fake_token")
    def test_valid_signature_returns_200(self, mock_token, mock_get):
        """Valid signature returns 200"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"key": self.public_key_pem}
        request = self.factory.post("/auth/ebay_market_delete/", data=self.fake_body, content_type="application/json", HTTP_X_EBAY_SIGNATURE=self.encoded_header)
        response = ebay_marketplace_deletion_notification(request)
        self.assertEqual(response.status_code, 200)

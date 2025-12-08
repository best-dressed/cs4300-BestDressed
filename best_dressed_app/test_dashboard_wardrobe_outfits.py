"""
Comprehensive test suite for Dashboard, Wardrobe, Account Settings, and Outfit features.

This test file covers:
- Dashboard view and functionality (with enhanced stats)
- Account Settings/User Profile management
- Wardrobe management (add, edit, delete, save from catalog, search, sort)
- Outfit creation and management (create, edit, delete, detail)
- Quick Actions (toggle favorite, duplicate, quick add to outfit)
- Smart Collections (favorites, seasons, occasions, recent, incomplete)
- Search and Filtering (outfit search, sort, combined filters)
- Model constraints and behavior
- Integration workflows
"""

# Third-party imports
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

# First-party imports
from best_dressed_app.models import Item, WardrobeItem, Outfit


# ==================== INTEGRATION TESTS ====================

class ItemDetailWithWardrobeTests(TestCase):
    """Tests for item detail view with wardrobe integration"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

        self.item = Item.objects.create(
            title="Test Item",
            description="Test description",
            image_url="https://example.com/item.jpg"
        )

    def test_item_detail_shows_already_saved_status(self):
        """Test that item detail shows if item is already in wardrobe"""
        self.client.login(username='testuser', password='testpass123')

        WardrobeItem.objects.create(
            user=self.user,
            title=self.item.title,
            catalog_item=self.item,
            category='other'
        )

        response = self.client.get(reverse('item_detail', kwargs={'pk': self.item.pk}))

        self.assertTrue(response.context['already_saved'])

    def test_item_detail_shows_not_saved_status(self):
        """Test that item detail shows if item is not yet in wardrobe"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(reverse('item_detail', kwargs={'pk': self.item.pk}))

        self.assertFalse(response.context['already_saved'])

    def test_item_detail_unauthenticated_no_save_status(self):
        """Test that unauthenticated users see appropriate state"""
        response = self.client.get(reverse('item_detail', kwargs={'pk': self.item.pk}))

        self.assertFalse(response.context['already_saved'])


class WardrobeIntegrationTests(TestCase):
    """Integration tests for wardrobe workflow"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

        self.catalog_item = Item.objects.create(
            title="Catalog Shirt",
            description="A nice shirt from the catalog",
            image_url="https://example.com/shirt.jpg"
        )

    def test_complete_wardrobe_workflow(self):
        """Test complete workflow: browse catalog, save item, view in wardrobe, edit, delete"""
        self.client.login(username='testuser', password='testpass123')

        # 1. Browse catalog and view item
        response = self.client.get(reverse('item_detail', kwargs={'pk': self.catalog_item.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['already_saved'])

        # 2. Save to wardrobe
        self.client.post(
            reverse('save_to_wardrobe', kwargs={'item_pk': self.catalog_item.pk}),
            follow=True
        )
        self.assertEqual(WardrobeItem.objects.filter(user=self.user).count(), 1)

        # 3. View in wardrobe
        response = self.client.get(reverse('my_wardrobe'))
        self.assertEqual(len(response.context['wardrobe_items']), 1)

        # 4. Edit the item
        wardrobe_item = WardrobeItem.objects.get(user=self.user)
        self.client.post(
            reverse('edit_wardrobe_item', kwargs={'item_pk': wardrobe_item.pk}),
            {
                'title': 'Updated Title',
                'category': 'top',
                'description': 'Updated description'
            }
        )
        wardrobe_item.refresh_from_db()
        self.assertEqual(wardrobe_item.title, 'Updated Title')

        # 5. Delete the item
        self.client.post(
            reverse('delete_wardrobe_item', kwargs={'item_pk': wardrobe_item.pk})
        )
        self.assertEqual(WardrobeItem.objects.filter(user=self.user).count(), 0)


class OutfitIntegrationTests(TestCase):
    """Integration tests for outfit creation workflow"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

    def test_complete_outfit_workflow(self):
        """Test complete workflow: add items to wardrobe, create outfit, view outfit"""
        self.client.login(username='testuser', password='testpass123')

        # 1. Add items to wardrobe
        self.client.post(reverse('add_wardrobe_item'), {
            'title': 'Blue Shirt',
            'category': 'top',
            'description': 'A blue shirt'
        })

        self.client.post(reverse('add_wardrobe_item'), {
            'title': 'Black Pants',
            'category': 'bottom',
            'description': 'Black pants'
        })

        self.assertEqual(WardrobeItem.objects.filter(user=self.user).count(), 2)

        # 2. Create outfit from wardrobe items
        items = WardrobeItem.objects.filter(user=self.user)
        self.client.post(reverse('create_outfit'), {
            'name': 'Work Outfit',
            'description': 'Professional look for work',
            'items': [item.pk for item in items],
            'occasion': 'business',
            'season': 'all'
        })

        self.assertEqual(Outfit.objects.filter(user=self.user).count(), 1)

        # 3. View outfit in my_outfits
        response = self.client.get(reverse('my_outfits'))
        self.assertEqual(len(response.context['outfits']), 1)

        outfit = response.context['outfits'][0]
        self.assertEqual(outfit.name, 'Work Outfit')
        self.assertEqual(outfit.items.count(), 2)


class CompleteWorkflowTests(TestCase):
    """Integration tests for complete user workflows"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

        self.catalog_item = Item.objects.create(
            title="Catalog Shirt",
            description="A nice shirt",
            image_url="https://example.com/shirt.jpg"
        )

    def test_complete_outfit_creation_workflow(self):
        """Test complete workflow from browsing catalog to creating outfit"""
        self.client.login(username='testuser', password='testpass123')

        # 1. Save catalog item to wardrobe
        self.client.post(
            reverse('save_to_wardrobe', kwargs={'item_pk': self.catalog_item.pk})
        )

        # 2. Verify item in wardrobe
        response = self.client.get(reverse('my_wardrobe'))
        self.assertEqual(len(response.context['wardrobe_items']), 1)

        # 3. Create outfit with wardrobe item
        item = WardrobeItem.objects.get(user=self.user)
        self.client.post(reverse('create_outfit'), {
            'name': 'New Outfit',
            'description': 'Test outfit',
            'items': [item.pk],
            'occasion': 'casual'
        })

        # 4. Verify outfit was created
        outfit = Outfit.objects.get(user=self.user)
        self.assertEqual(outfit.name, 'New Outfit')
        self.assertIn(item, outfit.items.all())

        # 5. View outfit detail
        response = self.client.get(
            reverse('outfit_detail', kwargs={'outfit_pk': outfit.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New Outfit')

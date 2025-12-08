"""
Comprehensive test suite for Outfit features.

This test file covers:
- Outfit creation and management (create, edit, delete, detail)
- Quick Actions (toggle favorite, duplicate, quick add to outfit)
- Smart Collections (favorites, seasons, occasions, recent, incomplete)
- Search and Filtering (outfit search, sort, combined filters)
- Model constraints and behavior
"""

import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from best_dressed_app.models import Item, WardrobeItem, Outfit


# ==================== OUTFIT TESTS ====================

class CreateOutfitTests(TestCase):
    """Tests for creating outfits"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

        self.item1 = WardrobeItem.objects.create(
            user=self.user,
            title="Shirt",
            category="top"
        )
        self.item2 = WardrobeItem.objects.create(
            user=self.user,
            title="Pants",
            category="bottom"
        )

    def test_create_outfit_requires_authentication(self):
        """Test that unauthenticated users cannot create outfits"""
        response = self.client.get(reverse('create_outfit'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_create_outfit_get_displays_form(self):
        """Test that GET request displays the create outfit form"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('create_outfit'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_outfit.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['mode'], 'create')

    def test_create_outfit_displays_user_wardrobe_items(self):
        """Test that form shows user's wardrobe items for selection"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('create_outfit'))

        wardrobe_items = response.context['wardrobe_items']
        self.assertEqual(len(wardrobe_items), 2)
        self.assertIn(self.item1, wardrobe_items)
        self.assertIn(self.item2, wardrobe_items)

    def test_create_outfit_post_creates_outfit(self):
        """Test that POST request creates a new outfit"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(reverse('create_outfit'), {
            'name': 'Casual Friday',
            'description': 'Perfect for casual work day',
            'items': [self.item1.pk, self.item2.pk],
            'occasion': 'casual',
            'season': 'all'
        })

        self.assertRedirects(response, reverse('my_outfits'))

        outfit = Outfit.objects.get(name='Casual Friday')
        self.assertEqual(outfit.user, self.user)
        self.assertEqual(outfit.items.count(), 2)
        self.assertIn(self.item1, outfit.items.all())
        self.assertIn(self.item2, outfit.items.all())

    def test_create_outfit_shows_success_message(self):
        """Test that success message is displayed after creation"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(reverse('create_outfit'), {
            'name': 'New Outfit',
            'description': 'Description',
            'items': [self.item1.pk]
        }, follow=True)

        messages_list = list(response.context['messages'])
        self.assertTrue(
            any('created successfully' in str(msg) for msg in messages_list)
        )


class MyOutfitsTests(TestCase):
    """Tests for viewing user's outfits with search and filtering"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

        self.item1 = WardrobeItem.objects.create(
            user=self.user,
            title="Shirt",
            category="top"
        )

        self.outfit1 = Outfit.objects.create(
            user=self.user,
            name="Casual Look",
            description="For everyday wear",
            occasion="casual",
            season="summer"
        )
        self.outfit1.items.add(self.item1)

        self.outfit2 = Outfit.objects.create(
            user=self.user,
            name="Formal Look",
            description="For special occasions",
            occasion="formal",
            season="winter",
            is_favorite=True
        )

    def test_my_outfits_requires_authentication(self):
        """Test that unauthenticated users cannot view outfits"""
        response = self.client.get(reverse('my_outfits'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_my_outfits_displays_user_outfits(self):
        """Test that page displays all user's outfits"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('my_outfits'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_outfits.html')

        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 2)
        self.assertIn(self.outfit1, outfits)
        self.assertIn(self.outfit2, outfits)

    def test_my_outfits_only_shows_user_outfits(self):
        """Test that users only see their own outfits"""
        user_model = get_user_model()
        other_user = user_model.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        other_outfit = Outfit.objects.create(
            user=other_user,
            name="Other User's Outfit"
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('my_outfits'))

        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 2)
        self.assertNotIn(other_outfit, outfits)

    def test_my_outfits_search_functionality(self):
        """Test searching outfits by name or description"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(reverse('my_outfits'), {'search': 'Casual'})

        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 1)
        self.assertEqual(outfits[0].name, "Casual Look")

    def test_my_outfits_sort_by_name(self):
        """Test sorting outfits by name"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(reverse('my_outfits'), {'sort': 'name'})
        outfits = list(response.context['outfits'])
        self.assertEqual(outfits[0].name, "Casual Look")
        self.assertEqual(outfits[1].name, "Formal Look")

        response = self.client.get(reverse('my_outfits'), {'sort': '-name'})
        outfits = list(response.context['outfits'])
        self.assertEqual(outfits[0].name, "Formal Look")
        self.assertEqual(outfits[1].name, "Casual Look")

    def test_my_outfits_favorites_filter(self):
        """Test filtering to show only favorites"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('my_outfits'),
            {'favorites': 'true'}
        )

        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 1)
        self.assertTrue(outfits[0].is_favorite)


class SmartCollectionsTests(TestCase):
    """Tests for smart collection filtering"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

        Outfit.objects.create(
            user=self.user,
            name="Summer Casual",
            season="summer",
            occasion="casual"
        )
        Outfit.objects.create(
            user=self.user,
            name="Winter Formal",
            season="winter",
            occasion="formal"
        )
        Outfit.objects.create(
            user=self.user,
            name="Work Outfit",
            occasion="business"
        )
        Outfit.objects.create(
            user=self.user,
            name="Date Night",
            occasion="date",
            is_favorite=True
        )

        self.recent_outfit = Outfit.objects.create(
            user=self.user,
            name="Recent Outfit"
        )

        old_outfit = Outfit.objects.create(
            user=self.user,
            name="Old Outfit"
        )
        old_outfit.created_at = timezone.now() - timedelta(days=31)
        old_outfit.save()

        item = WardrobeItem.objects.create(
            user=self.user,
            title="Shirt",
            category="top"
        )
        incomplete = Outfit.objects.create(user=self.user, name="Incomplete")
        incomplete.items.add(item)

    def test_favorites_collection(self):
        """Test favorites collection filter"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('my_outfits'),
            {'collection': 'favorites'}
        )

        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 1)
        self.assertEqual(outfits[0].name, "Date Night")

    def test_summer_collection(self):
        """Test summer season collection filter"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('my_outfits'),
            {'collection': 'summer'}
        )

        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 1)
        self.assertEqual(outfits[0].name, "Summer Casual")

    def test_formal_collection(self):
        """Test formal occasion collection filter"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('my_outfits'),
            {'collection': 'formal'}
        )

        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 1)
        self.assertEqual(outfits[0].name, "Winter Formal")

    def test_recent_collection(self):
        """Test recent collection (last 30 days)"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('my_outfits'),
            {'collection': 'recent'}
        )

        outfits = response.context['outfits']
        self.assertGreaterEqual(len(outfits), 6)
        self.assertIn(self.recent_outfit, outfits)

    def test_incomplete_collection(self):
        """Test incomplete collection (less than 3 items)"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('my_outfits'),
            {'collection': 'incomplete'}
        )

        outfits = response.context['outfits']
        self.assertGreaterEqual(len(outfits), 1)
        self.assertTrue(any(o.name == "Incomplete" for o in outfits))

    def test_collection_counts_in_context(self):
        """Test that collection counts are provided in context"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(reverse('my_outfits'))

        collection_counts = response.context['collection_counts']

        self.assertIn('favorites', collection_counts)
        self.assertIn('summer', collection_counts)
        self.assertIn('formal', collection_counts)
        self.assertIn('recent', collection_counts)
        self.assertIn('incomplete', collection_counts)

        self.assertEqual(collection_counts['favorites'], 1)
        self.assertEqual(collection_counts['summer'], 1)


class OutfitDetailTests(TestCase):
    """Tests for outfit detail view"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

        self.item1 = WardrobeItem.objects.create(
            user=self.user,
            title="Shirt",
            category="top"
        )

        self.outfit = Outfit.objects.create(
            user=self.user,
            name="Test Outfit",
            description="Test description",
            occasion="casual",
            season="summer"
        )
        self.outfit.items.add(self.item1)

    def test_outfit_detail_requires_authentication(self):
        """Test that unauthenticated users cannot view outfit details"""
        response = self.client.get(
            reverse('outfit_detail', kwargs={'outfit_pk': self.outfit.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_outfit_detail_displays_outfit(self):
        """Test that outfit detail page displays correct information"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('outfit_detail', kwargs={'outfit_pk': self.outfit.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'outfit_detail.html')
        self.assertEqual(response.context['outfit'], self.outfit)
        self.assertContains(response, "Test Outfit")
        self.assertContains(response, "Test description")

    def test_outfit_detail_user_can_only_view_own_outfits(self):
        """Test that users can only view their own outfits"""
        user_model = get_user_model()
        other_user = user_model.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )

        other_outfit = Outfit.objects.create(
            user=other_user,
            name="Other User's Outfit"
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('outfit_detail', kwargs={'outfit_pk': other_outfit.pk})
        )

        self.assertEqual(response.status_code, 404)


class EditOutfitTests(TestCase):
    """Tests for editing outfits"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

        self.item1 = WardrobeItem.objects.create(
            user=self.user,
            title="Shirt",
            category="top"
        )
        self.item2 = WardrobeItem.objects.create(
            user=self.user,
            title="Pants",
            category="bottom"
        )

        self.outfit = Outfit.objects.create(
            user=self.user,
            name="Original Name",
            description="Original description"
        )
        self.outfit.items.add(self.item1)

    def test_edit_outfit_requires_authentication(self):
        """Test that unauthenticated users cannot edit outfits"""
        response = self.client.get(
            reverse('edit_outfit', kwargs={'outfit_pk': self.outfit.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_edit_outfit_post_updates_outfit(self):
        """Test that POST request updates the outfit"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(
            reverse('edit_outfit', kwargs={'outfit_pk': self.outfit.pk}),
            {
                'name': 'Updated Name',
                'description': 'Updated description',
                'items': [self.item1.pk, self.item2.pk],
                'occasion': 'formal',
                'season': 'winter'
            }
        )

        self.assertRedirects(
            response,
            reverse('outfit_detail', kwargs={'outfit_pk': self.outfit.pk})
        )

        self.outfit.refresh_from_db()
        self.assertEqual(self.outfit.name, 'Updated Name')
        self.assertEqual(self.outfit.description, 'Updated description')
        self.assertEqual(self.outfit.items.count(), 2)


class DeleteOutfitTests(TestCase):
    """Tests for deleting outfits"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

        self.outfit = Outfit.objects.create(
            user=self.user,
            name="Outfit to Delete"
        )

    def test_delete_outfit_requires_authentication(self):
        """Test that unauthenticated users cannot delete outfits"""
        response = self.client.post(
            reverse('delete_outfit', kwargs={'outfit_pk': self.outfit.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_delete_outfit_post_deletes_outfit(self):
        """Test that POST request deletes the outfit"""
        self.client.login(username='testuser', password='testpass123')

        self.assertTrue(Outfit.objects.filter(pk=self.outfit.pk).exists())

        response = self.client.post(
            reverse('delete_outfit', kwargs={'outfit_pk': self.outfit.pk})
        )

        self.assertRedirects(response, reverse('my_outfits'))
        self.assertFalse(Outfit.objects.filter(pk=self.outfit.pk).exists())


# ==================== QUICK ACTIONS TESTS ====================

class ToggleFavoriteTests(TestCase):
    """Tests for toggling outfit favorite status (AJAX)"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

        self.outfit = Outfit.objects.create(
            user=self.user,
            name="Test Outfit",
            is_favorite=False
        )

    def test_toggle_favorite_requires_authentication(self):
        """Test that unauthenticated users cannot toggle favorites"""
        response = self.client.post(
            reverse(
                'toggle_outfit_favorite',
                kwargs={'outfit_pk': self.outfit.pk}
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_toggle_favorite_makes_favorite(self):
        """Test toggling from not favorite to favorite"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(
            reverse(
                'toggle_outfit_favorite',
                kwargs={'outfit_pk': self.outfit.pk}
            ),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertTrue(data['is_favorite'])

        self.outfit.refresh_from_db()
        self.assertTrue(self.outfit.is_favorite)

    def test_toggle_favorite_removes_favorite(self):
        """Test toggling from favorite to not favorite"""
        self.client.login(username='testuser', password='testpass123')

        self.outfit.is_favorite = True
        self.outfit.save()

        response = self.client.post(
            reverse(
                'toggle_outfit_favorite',
                kwargs={'outfit_pk': self.outfit.pk}
            ),
            content_type='application/json'
        )

        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertFalse(data['is_favorite'])

        self.outfit.refresh_from_db()
        self.assertFalse(self.outfit.is_favorite)


class DuplicateOutfitTests(TestCase):
    """Tests for duplicating outfits"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

        self.item1 = WardrobeItem.objects.create(
            user=self.user,
            title="Shirt",
            category="top"
        )

        self.outfit = Outfit.objects.create(
            user=self.user,
            name="Original Outfit",
            description="Original description",
            is_favorite=True
        )
        self.outfit.items.add(self.item1)

    def test_duplicate_outfit_requires_authentication(self):
        """Test that unauthenticated users cannot duplicate outfits"""
        response = self.client.post(
            reverse('duplicate_outfit', kwargs={'outfit_pk': self.outfit.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_duplicate_outfit_creates_copy(self):
        """Test that duplicating creates a new outfit with (Copy) suffix"""
        self.client.login(username='testuser', password='testpass123')

        self.client.post(
            reverse('duplicate_outfit', kwargs={'outfit_pk': self.outfit.pk})
        )

        self.assertEqual(Outfit.objects.filter(user=self.user).count(), 2)

        duplicate = Outfit.objects.get(name="Original Outfit (Copy)")
        self.assertEqual(duplicate.description, "Original description")
        self.assertEqual(duplicate.items.count(), 1)
        self.assertIn(self.item1, duplicate.items.all())

        self.assertFalse(duplicate.is_favorite)


class QuickAddToOutfitTests(TestCase):
    """Tests for quick add wardrobe item to outfit"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

        self.item = WardrobeItem.objects.create(
            user=self.user,
            title="Shirt",
            category="top"
        )

        self.outfit = Outfit.objects.create(
            user=self.user,
            name="Test Outfit"
        )

    def test_quick_add_requires_authentication(self):
        """Test that unauthenticated users cannot quick add"""
        response = self.client.get(
            reverse('quick_add_to_outfit', kwargs={'item_pk': self.item.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_quick_add_get_displays_outfit_list(self):
        """Test that GET request displays list of outfits"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('quick_add_to_outfit', kwargs={'item_pk': self.item.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'quick_add_to_outfit.html')
        self.assertEqual(response.context['wardrobe_item'], self.item)
        self.assertIn(self.outfit, response.context['outfits'])

    def test_quick_add_post_adds_item_to_outfit(self):
        """Test that POST request adds item to selected outfit"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(
            reverse('quick_add_to_outfit', kwargs={'item_pk': self.item.pk}),
            {'outfit_id': self.outfit.pk}
        )

        self.assertRedirects(response, reverse('my_wardrobe'))

        self.outfit.refresh_from_db()
        self.assertIn(self.item, self.outfit.items.all())

    def test_quick_add_prevents_duplicate_additions(self):
        """Test that adding same item twice shows info message"""
        self.client.login(username='testuser', password='testpass123')

        self.outfit.items.add(self.item)

        response = self.client.post(
            reverse('quick_add_to_outfit', kwargs={'item_pk': self.item.pk}),
            {'outfit_id': self.outfit.pk},
            follow=True
        )

        messages_list = list(response.context['messages'])
        self.assertTrue(any('already in' in str(msg) for msg in messages_list))


# ==================== MODEL TESTS ====================

class WardrobeModelTests(TestCase):
    """Tests for WardrobeItem model constraints and behavior"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.catalog_item = Item.objects.create(
            title="Test Item",
            description="Test description"
        )

    def test_wardrobe_item_string_representation(self):
        """Test the __str__ method returns correct format"""
        item = WardrobeItem.objects.create(
            user=self.user,
            title="Test Shirt",
            category="top"
        )

        self.assertEqual(str(item), "testuser - Test Shirt")

    def test_wardrobe_item_unique_together_constraint(self):
        """Test that unique_together constraint prevents duplicate saves"""
        WardrobeItem.objects.create(
            user=self.user,
            title="First Save",
            catalog_item=self.catalog_item,
            category="top"
        )

        with self.assertRaises(IntegrityError):
            WardrobeItem.objects.create(
                user=self.user,
                title="Second Save",
                catalog_item=self.catalog_item,
                category="top"
            )

    def test_wardrobe_item_catalog_item_nullable(self):
        """Test that catalog_item can be None for manually added items"""
        item = WardrobeItem.objects.create(
            user=self.user,
            title="Manual Item",
            category="top",
            catalog_item=None
        )

        self.assertIsNone(item.catalog_item)
        self.assertIsNotNone(item.pk)


class OutfitModelTests(TestCase):
    """Tests for Outfit model constraints and behavior"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.item1 = WardrobeItem.objects.create(
            user=self.user,
            title="Shirt",
            category="top"
        )

    def test_outfit_string_representation(self):
        """Test the __str__ method returns correct format"""
        outfit = Outfit.objects.create(
            user=self.user,
            name="Test Outfit"
        )

        self.assertEqual(str(outfit), "testuser - Test Outfit")

    def test_outfit_item_count_method(self):
        """Test the item_count helper method"""
        outfit = Outfit.objects.create(
            user=self.user,
            name="Test Outfit"
        )
        outfit.items.add(self.item1)

        self.assertEqual(outfit.item_count(), 1)

    def test_outfit_unique_name_per_user(self):
        """Test that outfit names must be unique per user"""
        Outfit.objects.create(
            user=self.user,
            name="Casual Look"
        )

        with self.assertRaises(IntegrityError):
            Outfit.objects.create(
                user=self.user,
                name="Casual Look"
            )

    def test_outfit_many_to_many_items(self):
        """Test that outfits can contain multiple items"""
        item2 = WardrobeItem.objects.create(
            user=self.user,
            title="Pants",
            category="bottom"
        )

        outfit = Outfit.objects.create(
            user=self.user,
            name="Complete Look"
        )
        outfit.items.add(self.item1, item2)

        self.assertEqual(outfit.items.count(), 2)
        self.assertIn(self.item1, outfit.items.all())
        self.assertIn(item2, outfit.items.all())

"""Tests for the forum app."""
# pylint: disable=no-member,too-many-instance-attributes
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from forum.models import Thread, Post


class ForumTests(TestCase):
    """Test cases for forum functionality."""

    def setUp(self):
        """Set up test data."""
        # users
        self.alice = User.objects.create_user(username="alice", password="pw")
        self.bob = User.objects.create_user(username="bob", password="pw")
        self.eve = User.objects.create_user(username="eve", password="pw")

        # normal thread + post
        self.thread = Thread.objects.create(
            title="Test thread",
            content="Thread body",
            user=self.alice
        )
        self.post = Post.objects.create(
            thread=self.thread,
            user=self.alice,
            content="Original reply"
        )

        # long unbroken content for wrapping/template checks
        self.long_word = "a" * 300
        self.wrap_thread = Thread.objects.create(
            title="WrapTest",
            content=self.long_word,
            user=self.bob
        )
        self.wrap_post = Post.objects.create(
            thread=self.wrap_thread,
            user=self.bob,
            content=self.long_word
        )

    def test_thread_str_and_relationship(self):
        """Test thread string representation and relationships."""
        self.assertIn("Test thread", str(self.thread))
        self.assertIn(self.alice.username, str(self.thread))
        self.assertEqual(self.thread.posts.count(), 1)
        self.assertEqual(self.thread.posts.first(), self.post)

    def test_post_str(self):
        """Test post string representation."""
        post_str = str(self.post)
        self.assertIn(self.alice.username, post_str)
        self.assertIn("Test thread", post_str)

    def test_threads_list_view(self):
        """Test threads list view."""
        url = reverse('threads')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.thread.title)

    def test_thread_detail_shows_thread_content_and_post(self):
        """Test thread detail view shows content and posts."""
        url = reverse('thread_detail', kwargs={'thread_id': self.thread.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Thread body")
        self.assertContains(resp, "Original reply")

    def test_post_reply_requires_login(self):
        """Test that posting a reply requires login."""
        url = reverse('thread_detail', kwargs={'thread_id': self.thread.id})
        self.client.post(url, data={'content': 'New reply'})
        self.assertEqual(
            Post.objects.filter(thread=self.thread, content='New reply').count(),
            0
        )

    def test_post_reply_when_logged_in(self):
        """Test posting a reply when logged in."""
        self.client.login(username=self.alice.username, password='pw')
        url = reverse('thread_detail', kwargs={'thread_id': self.thread.id})
        resp = self.client.post(url, data={'content': 'New reply'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            Post.objects.filter(thread=self.thread, content='New reply').exists()
        )

    def test_post_delete_only_by_author_or_staff(self):
        """Test that only post author or staff can delete posts."""
        del_url = reverse('post_delete', kwargs={'post_id': self.post.id})

        # non-author cannot delete
        self.client.login(username=self.eve.username, password='pw')
        self.client.post(del_url, follow=True)
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())

        # author can delete
        self.client.login(username=self.alice.username, password='pw')
        self.client.post(del_url, follow=True)
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())

    def test_post_edit_only_by_author_or_staff_and_edit_flow(self):
        """Test that only post author or staff can edit posts."""
        edit_url = reverse('post_edit', kwargs={'post_id': self.wrap_post.id})

        # non-author cannot access edit page
        self.client.login(username=self.eve.username, password='pw')
        resp = self.client.get(edit_url)
        if resp.status_code == 200:
            self.assertNotContains(resp, 'Edit Reply')
            self.assertNotContains(resp, '<form', html=False)
        else:
            # follow the redirect
            resp2 = self.client.get(edit_url, follow=True)
            self.assertNotContains(resp2, 'Edit Reply')

        # author can access and submit edit
        self.client.login(username=self.bob.username, password='pw')
        resp = self.client.get(edit_url)
        self.assertIn(resp.status_code, (200, 302))
        # POST the edit (author)
        self.client.post(edit_url, data={'content': 'Edited content'}, follow=True)
        self.wrap_post.refresh_from_db()
        self.assertEqual(self.wrap_post.content, 'Edited content')


class ThreadCreateTests(TestCase):
    """Test cases for thread creation."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

    def test_thread_create_success(self):
        """Test successful thread creation."""
        response = self.client.post(reverse('thread_create'), {
            'title': 'Test Thread',
            'content': 'This is a test thread.',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.first()
        self.assertEqual(thread.title, 'Test Thread')
        self.assertEqual(thread.content, 'This is a test thread.')
        self.assertEqual(thread.user, self.user)

    def test_thread_create_missing_title(self):
        """Test thread creation with missing title."""
        response = self.client.post(reverse('thread_create'), {
            'title': '',
            'description': 'Missing title test.',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Thread.objects.count(), 0)

    def test_thread_create_with_long_title(self):
        """Test thread creation with excessively long title."""
        long_title = 'A' * 300
        response = self.client.post(reverse('thread_create'), {
            'title': long_title,
            'description': 'Valid description',
        })
        self.assertEqual(response.status_code, 302)

    def test_thread_create_requires_login(self):
        """Test that thread creation requires login."""
        self.client.logout()
        response = self.client.get(reverse('thread_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class ThreadEditTests(TestCase):
    """Test cases for thread editing."""

    def setUp(self):
        """Set up test users and thread."""
        self.owner = User.objects.create_user(username='owner', password='pass')
        self.other_user = User.objects.create_user(username='intruder', password='pass')
        self.thread = Thread.objects.create(
            title='Original Title',
            content='Original description.',
            user=self.owner
        )

    def test_thread_edit_success(self):
        """Test successful thread edit."""
        self.client.login(username='owner', password='pass')
        response = self.client.post(reverse('thread_edit', args=[self.thread.pk]), {
            'title': 'Updated Title',
            'content': 'Updated description.',
        })
        self.assertEqual(response.status_code, 302)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.title, 'Updated Title')
        self.assertEqual(self.thread.content, 'Updated description.')

    def test_thread_edit_invalid_data(self):
        """Test thread edit with invalid data."""
        self.client.login(username='owner', password='pass')
        response = self.client.post(reverse('thread_edit', args=[self.thread.pk]), {
            'title': '',
            'description': 'Still here',
        })
        self.assertEqual(response.status_code, 302)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.title, 'Original Title')

    def test_thread_edit_preserves_creator(self):
        """Test that editing a thread preserves the original creator."""
        self.client.login(username='owner', password='pass')
        self.client.post(reverse('thread_edit', args=[self.thread.pk]), {
            'title': 'Changed title',
            'content': 'Changed description',
        })
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.user, self.owner)

    def test_thread_edit_unauthorized_user(self):
        """Test that unauthorized users cannot edit threads."""
        self.client.login(username='intruder', password='pass')
        response = self.client.get(reverse('thread_edit', args=[self.thread.pk]))
        self.assertEqual(response.status_code, 302)

    def test_thread_edit_requires_login(self):
        """Test that thread editing requires login."""
        response = self.client.get(reverse('thread_edit', args=[self.thread.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

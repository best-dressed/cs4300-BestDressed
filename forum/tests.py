from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from forum.models import Thread, Post

class ForumTests(TestCase):
    def setUp(self):
        # users
        self.alice = User.objects.create_user(username="alice", password="pw")
        self.bob = User.objects.create_user(username="bob", password="pw")
        self.eve = User.objects.create_user(username="eve", password="pw")

        # normal thread + post
        self.thread = Thread.objects.create(title="Test thread", content="Thread body", user=self.alice)
        self.post = Post.objects.create(thread=self.thread, user=self.alice, content="Original reply")

        # long unbroken content for wrapping/template checks
        self.long_word = "a" * 300
        self.wrap_thread = Thread.objects.create(title="WrapTest", content=self.long_word, user=self.bob)
        self.wrap_post = Post.objects.create(thread=self.wrap_thread, user=self.bob, content=self.long_word)

    # ---- Models ----
    def test_thread_str_and_relationship(self):
        self.assertIn("Test thread", str(self.thread))
        self.assertIn(self.alice.username, str(self.thread))
        self.assertEqual(self.thread.posts.count(), 1)
        self.assertEqual(self.thread.posts.first(), self.post)

    def test_post_str(self):
        # Adjusted: model __str__ returns "Post by <user> in <thread>"
        s = str(self.post)
        self.assertIn(self.alice.username, s)
        self.assertIn("Test thread", s)

    # ---- Views: listing and detail ----
    def test_threads_list_view(self):
        url = reverse('threads')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.thread.title)

    def test_thread_detail_shows_thread_content_and_post(self):
        url = reverse('thread_detail', kwargs={'thread_id': self.thread.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Thread body")
        self.assertContains(resp, "Original reply")

    # ---- Reply creation ----
    def test_post_reply_requires_login(self):
        url = reverse('thread_detail', kwargs={'thread_id': self.thread.id})
        self.client.post(url, data={'content': 'New reply'})
        self.assertEqual(Post.objects.filter(thread=self.thread, content='New reply').count(), 0)

    def test_post_reply_when_logged_in(self):
        self.client.login(username=self.alice.username, password='pw')
        url = reverse('thread_detail', kwargs={'thread_id': self.thread.id})
        resp = self.client.post(url, data={'content': 'New reply'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Post.objects.filter(thread=self.thread, content='New reply').exists())

    # ---- Post deletion permissions ----
    def test_post_delete_only_by_author_or_staff(self):
        del_url = reverse('post_delete', kwargs={'post_id': self.post.id})

        # non-author cannot delete
        self.client.login(username=self.eve.username, password='pw')
        resp = self.client.post(del_url, follow=True)
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())

        # author can delete
        self.client.login(username=self.alice.username, password='pw')
        resp = self.client.post(del_url, follow=True)
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())

    # ---- Post edit permissions and flow ----
    def test_post_edit_only_by_author_or_staff_and_edit_flow(self):
        edit_url = reverse('post_edit', kwargs={'post_id': self.wrap_post.id})

        # non-author cannot access edit page: expect redirect (302) or no permission
        self.client.login(username=self.eve.username, password='pw')
        resp = self.client.get(edit_url)
        # if view redirects to thread detail, status_code will be 302 (or 200 if not allowed)
        # assert we did not get the edit form page (check for a form element and an expected title)
        if resp.status_code == 200:
            self.assertNotContains(resp, 'Edit Reply')
            self.assertNotContains(resp, '<form', html=False)
        else:
            # follow the redirect and assert we end up on thread detail or login
            resp2 = self.client.get(edit_url, follow=True)
            self.assertNotContains(resp2, 'Edit Reply')

        # author can access and submit edit
        self.client.login(username=self.bob.username, password='pw')
        resp = self.client.get(edit_url)
        self.assertIn(resp.status_code, (200, 302))
        # POST the edit (author)
        resp = self.client.post(edit_url, data={'content': 'Edited content'}, follow=True)
        self.wrap_post.refresh_from_db()
        self.assertEqual(self.wrap_post.content, 'Edited content')
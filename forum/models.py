"""Models for the forum app."""
# pylint: disable=too-few-public-methods,no-member
from django.db import models
from django.contrib.auth.models import User
from best_dressed_app.models import Outfit


class Thread(models.Model):
    """Model representing a forum thread."""
    title = models.CharField(max_length=255)
    content = models.TextField(default='')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='threads')
    created_at = models.DateTimeField(auto_now_add=True)

    attached_outfit = models.ForeignKey(
        Outfit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='forum_threads',
        help_text="Optional outfit to attach to this thread"
    )

    def __str__(self):
        return f"Thread: {self.title} by {self.user.username}"

    def like_count(self):
        """Return the number of likes on this thread."""
        return self.thread_likes.count()

    def is_liked_by(self, user):
        """Check if the given user has liked this thread."""
        if user.is_authenticated:
            return self.thread_likes.filter(user=user).exists()
        return False

    def is_saved_by(self, user):
        """Check if the given user has saved this thread."""
        if user.is_authenticated:
            return self.saved_by.filter(user=user).exists()
        return False

    def save_count(self):
        """Return the number of times this thread has been saved."""
        return self.saved_by.count()


class Post(models.Model):
    """Model representing a post in a forum thread."""
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='posts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post by {self.user.username} in {self.thread.title}"

    def like_count(self):
        """Return the number of likes on this post."""
        return self.post_likes.count()

    def is_liked_by(self, user):
        """Check if the given user has liked this post."""
        if user.is_authenticated:
            return self.post_likes.filter(user=user).exists()
        return False


class ThreadLike(models.Model):
    """Model representing a user's like on a thread."""
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='thread_likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='thread_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta options for ThreadLike."""
        unique_together = ('thread', 'user')

    def __str__(self):
        return f"{self.user.username} likes {self.thread.title}"


class PostLike(models.Model):
    """Model representing a user's like on a post."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta options for PostLike."""
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user.username} likes post {self.post.id}"


class SavedThread(models.Model):
    """Model representing a user's saved thread."""
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='saved_by')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_threads')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta options for SavedThread."""
        unique_together = ('thread', 'user')

    def __str__(self):
        return f"{self.user.username} saved {self.thread.title}"

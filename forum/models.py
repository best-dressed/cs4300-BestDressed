# Create your models here.
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class Thread(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField(default='')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='threads')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Thread: {self.title} by {self.user.username}"
    
    def like_count(self):
        return self.thread_likes.count()
    
    def is_liked_by(self, user):
        if user.is_authenticated:
            return self.thread_likes.filter(user=user).exists()
        return False

class Post(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='posts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post by {self.user.username} in {self.thread.title}"
    
    def like_count(self):
        return self.post_likes.count()
    
    def is_liked_by(self, user):
        if user.is_authenticated:
            return self.post_likes.filter(user=user).exists()
        return False

# NEW: Like models
class ThreadLike(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='thread_likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='thread_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('thread', 'user')  # User can only like once

    def __str__(self):
        return f"{self.user.username} likes {self.thread.title}"

class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')  # User can only like once

    def __str__(self):
        return f"{self.user.username} likes post {self.post.id}"
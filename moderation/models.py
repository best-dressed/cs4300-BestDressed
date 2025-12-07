"""
Models for moderation tools, mainly used to track bans
"""
from django.db import models
from django.utils import timezone

class BannedIP(models.Model):
    """A banned IP address, used to check if a poster's IP has been
    banned
    """
    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.TextField(blank=True, null=True)
    banned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)  # new field
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Banned IP"
        verbose_name_plural = "Banned IPs"
        ordering = ["-banned_at"]

    def __str__(self):
        return f"{self.ip_address} (active={self.is_active()})"

    def is_active(self):
        """
        Check if the ban is still active.
        - active flag must be True
        - expires_at must be None or in the future
        """
        if not self.active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

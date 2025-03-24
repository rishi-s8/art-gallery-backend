import uuid
import secrets
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField

User = get_user_model()

class Webhook(models.Model):
    """
    Model for webhook configurations.
    """
    EVENT_CHOICES = [
        ('server.created', 'Server Created'),
        ('server.updated', 'Server Updated'),
        ('server.deleted', 'Server Deleted'),
        ('server.verified', 'Server Verified'),
        ('verification.requested', 'Verification Requested'),
        ('verification.completed', 'Verification Completed'),
        ('server.status_changed', 'Server Status Changed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webhooks')

    url = models.URLField()
    events = ArrayField(
        models.CharField(max_length=50, choices=EVENT_CHOICES),
        default=list
    )

    description = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)

    # Secret for signing webhook payloads
    secret = models.CharField(max_length=64)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Webhook {self.id} for {self.owner.email}"

    def save(self, *args, **kwargs):
        """Generate a secret if one doesn't exist."""
        if not self.secret:
            self.secret = secrets.token_hex(32)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['active']),
        ]


class WebhookDelivery(models.Model):
    """
    Model for tracking webhook delivery attempts.
    """
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, related_name='deliveries')

    event = models.CharField(max_length=50)
    payload = models.JSONField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    attempt_count = models.PositiveSmallIntegerField(default=0)
    response_code = models.PositiveSmallIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Webhook Delivery {self.id} ({self.status})"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['webhook', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['event']),
        ]
        verbose_name_plural = "Webhook deliveries"
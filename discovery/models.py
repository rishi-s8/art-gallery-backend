import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField

User = get_user_model()

class SearchHistory(models.Model):
    """
    Model to track user search history.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    query = models.CharField(max_length=255)
    filters = models.JSONField(default=dict, blank=True)
    results_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.query}"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Search histories"
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]


class ServerUsage(models.Model):
    """
    Model to track user interactions with servers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='server_usage')
    server = models.ForeignKey('servers.Server', on_delete=models.CASCADE, related_name='usage_records')
    capability = models.CharField(max_length=255, blank=True, null=True)
    parameters = models.JSONField(default=dict, blank=True)
    successful = models.BooleanField(default=True)
    response_time = models.FloatField()  # in milliseconds
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.server.name}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['server', '-created_at']),
        ]

    def save(self, *args, **kwargs):
        """Update server usage count when a new usage record is created."""
        super().save(*args, **kwargs)

        # Increment server usage count
        self.server.usage_count += 1
        self.server.save(update_fields=['usage_count'])


class UserPreference(models.Model):
    """
    Model to store user preferences for recommendations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    preferred_types = ArrayField(
        models.CharField(max_length=10),
        default=list,
        blank=True
    )
    preferred_tags = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True
    )
    excluded_servers = models.ManyToManyField('servers.Server', related_name='excluded_by', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} Preferences"
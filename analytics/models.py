import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField

class ServerAnalytics(models.Model):
    """
    Model for daily server usage analytics.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    server = models.ForeignKey('servers.Server', on_delete=models.CASCADE, related_name='analytics')

    date = models.DateField()
    total_requests = models.PositiveIntegerField(default=0)
    unique_clients = models.PositiveIntegerField(default=0)
    avg_response_time_ms = models.FloatField(default=0)
    error_count = models.PositiveIntegerField(default=0)

    # Distribution of status codes
    status_2xx = models.PositiveIntegerField(default=0)
    status_3xx = models.PositiveIntegerField(default=0)
    status_4xx = models.PositiveIntegerField(default=0)
    status_5xx = models.PositiveIntegerField(default=0)

    # Most used capabilities
    top_capabilities = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.server.name} - {self.date}"

    @property
    def error_rate(self):
        """Calculate error rate as a percentage."""
        if self.total_requests == 0:
            return 0
        return (self.error_count / self.total_requests) * 100

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['server', 'date']),
        ]
        unique_together = ['server', 'date']
        verbose_name_plural = "Server analytics"


class RequestLog(models.Model):
    """
    Model for individual request logs (for detailed analytics).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    server = models.ForeignKey('servers.Server', on_delete=models.CASCADE, related_name='request_logs')

    client_id = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField()
    capability = models.CharField(max_length=255, null=True, blank=True)

    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    response_time_ms = models.FloatField()

    # Client metadata
    user_agent = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country_code = models.CharField(max_length=2, null=True, blank=True)

    # Request details (optional, for debugging)
    request_headers = models.JSONField(default=dict, blank=True)
    request_body = models.JSONField(default=dict, blank=True)

    is_error = models.BooleanField(default=False)
    error_details = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.server.name} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['server', '-timestamp']),
            models.Index(fields=['server', 'client_id']),
            models.Index(fields=['server', 'capability']),
            models.Index(fields=['server', 'is_error']),
        ]


class NetworkAnalytics(models.Model):
    """
    Model for network-wide analytics.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True)

    total_servers = models.PositiveIntegerField(default=0)
    active_servers = models.PositiveIntegerField(default=0)
    total_requests = models.PositiveIntegerField(default=0)
    unique_clients = models.PositiveIntegerField(default=0)
    new_servers = models.PositiveIntegerField(default=0)

    # Distribution by server type
    agent_count = models.PositiveIntegerField(default=0)
    resource_count = models.PositiveIntegerField(default=0)
    tool_count = models.PositiveIntegerField(default=0)

    # Top tags across the network
    top_tags = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Network Analytics - {self.date}"

    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Network analytics"


class ClientTrafficLog(models.Model):
    """
    Model for tracking traffic patterns by client.
    Anonymized for privacy.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_id = models.CharField(max_length=255)  # Hashed identifier

    date = models.DateField()
    servers_accessed = ArrayField(
        models.UUIDField(),
        default=list,
        blank=True
    )
    total_requests = models.PositiveIntegerField(default=0)

    # Most used capabilities
    top_capabilities = models.JSONField(default=dict, blank=True)

    # Geographical data (if available)
    country_code = models.CharField(max_length=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Client Traffic - {self.client_id[:8]}... - {self.date}"

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['client_id', '-date']),
        ]
        unique_together = ['client_id', 'date']
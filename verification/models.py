import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings

class VerificationRequest(models.Model):
    """
    Model for server verification requests.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    server = models.ForeignKey('servers.Server', on_delete=models.CASCADE, related_name='verification_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Verification token for domain verification
    verification_token = models.CharField(max_length=100, unique=True)
    verification_token_expiry = models.DateTimeField()

    # Verification method used
    VERIFICATION_METHOD_CHOICES = [
        ('dns', 'DNS Record'),
        ('file', 'File Upload'),
        ('meta_tag', 'Meta Tag'),
    ]
    verification_method = models.CharField(
        max_length=10,
        choices=VERIFICATION_METHOD_CHOICES,
        null=True,
        blank=True
    )
    verification_proof = models.TextField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.server.name} Verification - {self.status}"

    def is_token_valid(self):
        """Check if the verification token is still valid."""
        return timezone.now() < self.verification_token_expiry

    def generate_verification_token(self):
        """Generate a new verification token."""
        import secrets
        self.verification_token = secrets.token_urlsafe(32)
        self.verification_token_expiry = timezone.now() + settings.VERIFICATION_TOKEN_EXPIRY
        self.save()
        return self.verification_token

    def complete_verification(self, success=True):
        """Mark the verification request as completed."""
        self.status = 'completed' if success else 'failed'
        self.completed_at = timezone.now()
        self.save()

        if success:
            # Update server verified status
            self.server.verified = True
            self.server.save()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['server', 'status']),
            models.Index(fields=['verification_token']),
        ]


class VerificationCheck(models.Model):
    """
    Model for individual verification checks performed on a server.
    """
    CHECK_TYPE_CHOICES = [
        ('ownership', 'Ownership Verification'),
        ('health', 'Health Check'),
        ('capabilities', 'Capabilities Check'),
        ('security', 'Security Assessment'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verification_request = models.ForeignKey(VerificationRequest, on_delete=models.CASCADE, related_name='checks')

    check_type = models.CharField(max_length=20, choices=CHECK_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    details = models.JSONField(default=dict, blank=True)
    message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.verification_request.server.name} - {self.check_type} - {self.status}"

    class Meta:
        ordering = ['check_type']
        unique_together = ['verification_request', 'check_type']


class HealthCheck(models.Model):
    """
    Model to track server health checks over time.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    server = models.ForeignKey('servers.Server', on_delete=models.CASCADE, related_name='health_checks')

    is_up = models.BooleanField()
    response_time = models.FloatField()  # in seconds
    status_code = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    # Health check details (e.g. capabilities tested, etc.)
    details = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.server.name} Health Check - {'Up' if self.is_up else 'Down'}"

    def save(self, *args, **kwargs):
        """Update server uptime statistics when a new health check is recorded."""
        super().save(*args, **kwargs)

        # Update server uptime percentage
        # Calculate based on the last 30 days of health checks
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_checks = HealthCheck.objects.filter(
            server=self.server,
            created_at__gte=thirty_days_ago
        )

        total_checks = recent_checks.count()
        if total_checks > 0:
            up_checks = recent_checks.filter(is_up=True).count()
            uptime_percentage = (up_checks / total_checks) * 100

            self.server.uptime = uptime_percentage
            self.server.last_checked = self.created_at

            if not self.is_up and self.server.is_active:
                self.server.status_message = "Down during automatic health check"
                self.server.is_active = False
            elif self.is_up and not self.server.is_active:
                self.server.status_message = "Restored during automatic health check"
                self.server.is_active = True

            self.server.save()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['server', '-created_at']),
            models.Index(fields=['is_up']),
        ]